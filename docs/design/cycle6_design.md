# サイクル6 設計書

対象：[cycle6_requirements.md](../requirements/cycle6_requirements.md) FR-39〜41
（フェーズ1：全上場企業マスタの一括登録）

実装順：FR-40（スキーマ変更）→ FR-39（一括登録バッチ）→ FR-41（フロント表示調整）
（FR-40はFR-39・FR-41の両方が依存する前提のため最初に設計・実装する）

---

## 1. FR-40：`companies.accounting_standard`をNULL許容にするスキーマ変更

### Alembicマイグレーション（新規）

SQLiteは`ALTER TABLE ... ALTER COLUMN`で列制約を変更できないため、既存の全マイグレーション
（`94452a3cdebf`・`62c510634352`）と同じ「生DDLを`op.execute`で書く」方式を踏襲しつつ、
「新スキーマでテーブルを作り直し、データをコピーし、旧テーブルを消す」という
SQLiteの標準的な回避策を使う。

```python
"""make companies.accounting_standard nullable

FR-39（全上場企業マスタの一括登録）で、財務データ未取得（＝accounting_standardが
判明していない）企業も登録できるようにするため、NOT NULL制約を外す
（docs/requirements/cycle6_requirements.md FR-40）。

Revision ID: <alembicが自動生成>
Revises: 62c510634352
Create Date: ...
"""
from alembic import op


def upgrade() -> None:
    """Upgrade schema."""
    op.execute("ALTER TABLE companies RENAME TO companies_old")
    op.execute(
        """
        CREATE TABLE companies (
            code VARCHAR(10) PRIMARY KEY NOT NULL,
            name VARCHAR(255) NOT NULL,
            sector VARCHAR(100),
            accounting_standard VARCHAR(50)
        )
        """
    )
    op.execute("INSERT INTO companies SELECT code, name, sector, accounting_standard FROM companies_old")
    op.execute("DROP TABLE companies_old")


def downgrade() -> None:
    """Downgrade schema."""
    op.execute("ALTER TABLE companies RENAME TO companies_old")
    op.execute(
        """
        CREATE TABLE companies (
            code VARCHAR(10) PRIMARY KEY NOT NULL,
            name VARCHAR(255) NOT NULL,
            sector VARCHAR(100),
            accounting_standard VARCHAR(50) NOT NULL
        )
        """
    )
    op.execute("INSERT INTO companies SELECT code, name, sector, accounting_standard FROM companies_old")
    op.execute("DROP TABLE companies_old")
```

`facts`テーブルの`FOREIGN KEY (company_code) REFERENCES companies (code)`はテーブル名参照で
あり、`companies`を同名で作り直す限り壊れない（SQLiteはデフォルトで外部キー制約の実施が
無効なため、本マイグレーションでも特別な考慮は不要。既存コードでも`PRAGMA foreign_keys`は
有効化されていないことを確認済み）。

`downgrade()`は、既にNULLの行がある状態で実行すると`NOT NULL`制約違反になる
（意図的：ロールバック時にNULLデータが残っていることに気づけるようにするため、
黙ってデータを落とす実装にはしない）。

### `backend/database.py`

```diff
  class Company(Base):
      """TBL-001 companies"""

      __tablename__ = "companies"

      code: Mapped[str] = mapped_column(String(10), primary_key=True)
      name: Mapped[str] = mapped_column(String(255), nullable=False)
      sector: Mapped[str | None] = mapped_column(String(100), nullable=True)
-     accounting_standard: Mapped[str] = mapped_column(String(50), nullable=False)
+     accounting_standard: Mapped[str | None] = mapped_column(String(50), nullable=True)
```

### `backend/schemas.py`

```diff
  class Company(BaseModel):
      """docs/design/api/components/schemas/Company.yaml"""

      code: str
      name: str
      sector: str | None = None
-     accounting_standard: str
+     accounting_standard: str | None = None
      periods: list[date]
```

### `docs/design/api/components/schemas/Company.yaml`

`accounting_standard`を`required`から外し、`nullable: true`（またはOpenAPI 3.0の
`type: [string, "null"]`相当の書き方）に変更する。

### `docs/design/table/TBL-001_companies.md`

`accounting_standard`カラムの「必須」列（✓）を外し、備考に「財務データ未取得の企業は
NULL（サイクル6 FR-40）」という一文を追記する。

### 既存コードへの影響確認

- `routers/edinet.py`の`_upsert_company`：`accounting_standard`に常に実際の値
  （XBRL解析結果）を渡しているため、この関数自体の変更は不要
- `routers/companies.py`：`schemas.Company(accounting_standard=company.accounting_standard, ...)`
  は型が`str`→`str | None`に変わるだけで、`company.accounting_standard`が`None`の場合も
  そのまま渡せば型エラーにならない（コード変更不要）

---

## 2. FR-39：全上場企業マスタの一括登録バッチ

### `backend/edinet_client.py`：公開関数の追加

`_load_filer_info_cache()`は private（アンダースコア始まり）で`search_filers`・
`fetch_filer_info`の内部実装用。バッチスクリプトから直接privateな関数を呼ばせず、
公開のラッパー関数を1つ追加する。

```python
def list_all_filers() -> list[FilerInfo]:
    """EDINETコードリストの全提出者を返す（サイクル6 FR-39、一括登録バッチ用）"""
    return _load_filer_info_cache()
```

### `backend/scripts/__init__.py`（新規、空ファイル）

`python -m scripts.bulk_register_companies`で実行するため、既存の`routers/__init__.py`と
同じパターンで`scripts`を明示的なパッケージにする。

### `backend/scripts/bulk_register_companies.py`（新規）

```python
"""全上場企業の基本情報をcompaniesテーブルに一括登録する（サイクル6 FR-39）。

実行方法：backend/ディレクトリで `python -m scripts.bulk_register_companies`
1回限りの手動実行想定。再実行しても同じ結果になる（冪等）。
"""
import logging

from database import Company, SessionLocal
from edinet_client import list_all_filers

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)


def _to_company_code(sec_code: str) -> str:
    """EDINETの証券コード（5桁、末尾0）を、companiesテーブルの4桁codeに変換する。

    既存の`memo/リクルートデータ取得メモ.md`・`docs/design/table/TBL-001_companies.md`の
    変換ルール（末尾の0を除去）と同じ。サイクル6設計時に実データ3,829件全件で
    末尾が'0'であることを確認済み（想定外のケースは想定していない）。
    """
    if not sec_code.endswith("0"):
        raise ValueError(f"末尾が0でない証券コード: {sec_code}")
    return sec_code[:-1]


def main() -> None:
    filers = list_all_filers()
    registered = 0
    skipped_no_sec_code = 0
    skipped_error = 0

    with SessionLocal() as session:
        for filer in filers:
            if filer.sec_code is None:
                skipped_no_sec_code += 1
                continue
            try:
                code = _to_company_code(filer.sec_code)
                company = session.get(Company, code)
                if company is None:
                    company = Company(code=code)
                    session.add(company)
                company.name = filer.name
                company.sector = filer.sector
                # accounting_standardは更新しない（財務データ取得済みなら既存値を維持、
                # 未取得ならNoneのまま。FR-39は基本情報のみを対象とするため）
                registered += 1
            except Exception:
                logger.exception("企業登録に失敗しました: edinet_code=%s", filer.edinet_code)
                skipped_error += 1
                continue

        session.commit()

    logger.info(
        "完了: 登録/更新=%d件, sec_codeなしでスキップ=%d件, エラーでスキップ=%d件",
        registered, skipped_no_sec_code, skipped_error,
    )


if __name__ == "__main__":
    main()
```

**設計判断のポイント**：

- `session.get(Company, filer.sec_code)`で既存行の有無を見て、あれば更新・なければ新規作成する
  （SQLAlchemyの`merge`ではなく`get`+手動更新にしたのは、`accounting_standard`を**上書きしない**
  という要件（FR-39は基本情報のみを対象とし、既にダウンロード済みで`accounting_standard`が
  設定されている企業の値を空で潰さない）を明示的にコードで表現するため）
- 1社ごとの例外は`try/except`でスキップしログに残し、バッチ全体を止めない
  （要件定義FR-39の追記事項に対応）
- `sec_code`の重複について、設計時点で実データを確認した（`edinet_client.list_all_filers()`
  を実行し検証）：全11,350件中`sec_code`を持つ3,829件に重複は**0件**（2026-07-22時点、
  NFR-15）。4桁への変換（`_to_company_code`）後も3,829件がすべてユニークであることを
  確認済み。現時点では実害はないが、将来のEDINET側データ変化に備えて`session.get`＋上書き
  （**後から処理された行の`name`/`sector`が勝つ**設計）のまま、フェイルセーフとして残す
- **`sec_code`（5桁、末尾0）→`companies.code`（4桁）の変換が必要**（設計時に実装を書く前の
  実データ検証で発見。既存の`TBL-001_companies.md`にこの変換ルール自体は記載済みだったが、
  当初のバッチ設計案で変換を入れ忘れていた）。全3,829件で末尾が`0`であることを確認済み
  （`_to_company_code`参照）

---

## 3. FR-41：企業一覧・詳細画面での「データ未取得」表示

### `frontend/src/api/client.ts`

```diff
  export type Company = {
    code: string;
    name: string;
    sector: string | null;
-   accounting_standard: string;
+   accounting_standard: string | null;
    periods: string[];
  };
```

### `frontend/src/pages/CompanyListPage.tsx`

```diff
                  <p className="text-sm text-gray-500">
-                   {company.code} ｜ {company.sector ?? "業種不明"} ｜{" "}
-                   {company.accounting_standard}
+                   {company.code} ｜ {company.sector ?? "業種不明"} ｜{" "}
+                   {company.accounting_standard ?? "データ未取得"}
                  </p>
```

### `frontend/src/pages/CompanyDetailPage.tsx`

会計基準表示部分：

```diff
            <p className="text-gray-500">
-             会計基準：{financials.company.accounting_standard}
+             会計基準：{financials.company.accounting_standard ?? "データ未取得"}
            </p>
```

財務データ0件時の空状態（**現状は何も表示されない**ことを実機コード確認済み、
`cycle6_requirements.md` FR-41参照）：

```diff
-       {financials.data.length > 0 && (
-         <>
-           <div className="grid grid-cols-1 gap-6 xl:grid-cols-2">
-             ...B/S・P/L・CF・財務分析指標...
-           </div>
-         </>
-       )}
+       {financials.data.length > 0 ? (
+         <>
+           <div className="grid grid-cols-1 gap-6 xl:grid-cols-2">
+             ...B/S・P/L・CF・財務分析指標（変更なし）...
+           </div>
+         </>
+       ) : (
+         <Panel className="space-y-3 text-center">
+           <p className="text-gray-500">
+             まだ財務データを取得していません
+           </p>
+           <Button onClick={() => navigate("/download")}>
+             データを取得する
+           </Button>
+         </Panel>
+       )}
```

`Panel`・`Button`は既存のサイクル4/5コンポーネントをそのまま使う（新規コンポーネントは
作らない）。`navigate`は`CompanyDetailPage`で既に`useNavigate()`から取得済みのため
追加の依存はない。

---

## 4. 変更ファイル一覧

| ファイル | 変更内容 | 関連FR |
|---|---|---|
| `backend/alembic/versions/<new>.py` | `companies.accounting_standard`をNULL許容にするマイグレーション（新規） | FR-40 |
| `backend/database.py` | `Company.accounting_standard`の型変更 | FR-40 |
| `backend/schemas.py` | `Company.accounting_standard`の型変更 | FR-40 |
| `docs/design/api/components/schemas/Company.yaml` | `accounting_standard`を必須から外す | FR-40 |
| `docs/design/table/TBL-001_companies.md` | カラム定義表の更新 | FR-40 |
| `backend/edinet_client.py` | `list_all_filers()`公開関数を追加 | FR-39 |
| `backend/scripts/__init__.py` | 新規（空ファイル、パッケージ化） | FR-39 |
| `backend/scripts/bulk_register_companies.py` | 一括登録バッチ（新規） | FR-39 |
| `frontend/src/api/client.ts` | `Company.accounting_standard`の型変更 | FR-41 |
| `frontend/src/pages/CompanyListPage.tsx` | 会計基準の代替表示 | FR-41 |
| `frontend/src/pages/CompanyDetailPage.tsx` | 会計基準の代替表示、財務データ0件時の空状態UI | FR-41 |

---

## 5. 動作確認方針

- `backend/scripts/bulk_register_companies.py`は実際にEDINETコードリストを取得して
  実行し、`companies`テーブルの登録件数・`sec_code`なしでスキップした件数・
  エラー件数をログで確認する（モックなし、実データで検証）
- 既存のダウンロード機能（個別企業のダウンロード）が、一括登録後も壊れずに動作することを
  実機確認する（NFR-13）
- フロントエンドは、財務データ0件の企業（一括登録直後の企業）と、既存のダウンロード済み
  企業の両方で表示を確認する
