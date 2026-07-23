# サイクル13 設計書（UC-1-1）

対象：[cycle13_requirements.md](../requirements/cycle13_requirements.md) FR-57・
FR-58・FR-59・FR-60（UC-1-1のみ）

設計順：画面フロー→画面→API→バッチ（[cycle-workflow](../../.claude/skills/cycle-workflow/SKILL.md)の
ユースケース単位運用に基づく）。FR-59（命名是正）はFR-58の一部として、
テーブル新設と同時に既存`facts`のリネームも行う。

---

## 1. 画面フローの整理

UC-1-1は新規画面・新規遷移を伴わない。既存のSCR-002（企業一覧）→SCR-003
（企業詳細）という画面フローに変更はない。FR-57はSCR-003の画面定義書の是正、
FR-58はSCR-003への「定性情報」セクションの追加であり、いずれもSCR-003内で完結する。

---

## 2. 画面の整理

### FR-57：SCR-003画面定義書の是正

`docs/design/screen/items/SCR-003_items.md`を、`CompanyDetailPage.tsx`の実装に
合わせて全面更新する（作業済み）。追加した項目：

| 項目ID | 画面項目名 | 表示位置 | 参照元API | 備考 |
|---|---|---|---|---|
| SCR-003-13 | 貸借対照表（B/S）セクション見出し・グラフ | B/S・P/L 2カラムの左 | API-COM-002 | `FinancialMetricSection`。`BS_METRIC_DEFINITIONS`使用 |
| SCR-003-14 | 損益計算書（P/L）セクション見出し・グラフ | B/S・P/L 2カラムの右 | API-COM-002 | `FinancialMetricSection`。`PL_METRIC_DEFINITIONS`使用 |
| SCR-003-15 | 財務分析指標：収益性セクション | 財務分析指標エリア | API-COM-005 | `RatioCategorySection`。`PROFITABILITY_RATIOS`使用 |
| SCR-003-16 | 財務分析指標：効率性セクション | 同上 | API-COM-005 | `EFFICIENCY_RATIOS`使用 |
| SCR-003-17 | 財務分析指標：安全性セクション | 同上 | API-COM-005 | `SAFETY_RATIOS`使用 |
| SCR-003-18 | 財務分析指標：投資指標セクション | 同上 | API-COM-005 | `INVESTMENT_RATIOS`使用 |

既存のSCR-003-06/07（グラフの横軸・棒）は、B/S・P/L2セクション分離後の実態に
合わせて記述を修正済み。

### FR-58：定性情報セクションの追加

SCR-003の画面下部（財務分析指標セクションの後）に、新しい「定性情報」セクションを
追加する。定性情報はB/S・P/Lグラフの年度範囲選択（SCR-003-05）とは別に、専用の
単一年度セレクタを持つ。過去の年度を選んで当時の開示内容を遡って確認できる。
初期値は最新年度。

| 項目ID | 画面項目名 | 表示位置 | 参照元API | 表示形式 |
|---|---|---|---|---|
| SCR-003-19 | 定性情報セクション見出し | 財務分析指標の後 | なし | 「定性情報」 |
| SCR-003-20 | 定性情報：年度セレクタ（単一） | 定性情報セクション見出しの下 | API-COM-006（`available_periods`） | 年セレクタ1つ。B/S・P/Lの年度範囲選択（SCR-003-05）とは独立。選択変更のたびにAPI-COM-006を`period_end`指定で再呼び出しする。初期値は`available_periods`の最新年度 |
| SCR-003-21 | 事業の内容（開閉式） | 定性情報セクション内 | API-COM-006 | デフォルト閉、クリックで展開 |
| SCR-003-22 | 事業等のリスク（開閉式） | 同上 | API-COM-006 | デフォルト閉 |
| SCR-003-23 | 経営者による分析（MD&A、開閉式） | 同上 | API-COM-006 | デフォルト閉 |
| SCR-003-24 | 定性情報なし時の表示 | 同上 | API-COM-006 | 選択年度の3項目とも空の場合「この年度の定性情報はありません」。対象企業に開示書類が1件もない場合はセクション自体を非表示（年度セレクタも表示しない） |

新規コンポーネント`frontend/src/components/QualitativeFactSection.tsx`
（開閉式の1項目を表示する共通コンポーネント）を作成し、3項目（事業の内容・
リスク・MD&A）で使い回す。

---

## 3. APIの整理

### 新規：`API-COM-006` `GET /api/companies/{code}/qualitative-facts?period_end=`

**EDINETアクセスの原則（ユーザー確認済み）**：本APIはEDINETに一切アクセスせず、
`company_qualitative_facts`テーブル（DB）から読み取るのみ。EDINETへの通信は
バッチ処理（`BATCH-005`・今後の日次バッチ）のみで発生させ、ユーザーの画面操作を
契機にEDINETへアクセスすることはない（サイクル9で確立した「画面はDBのみ参照」の
原則を維持する、既存の`API-COM-002/003/005`と同じ設計方針）。

- `period_end`省略時：`documents`テーブルで`period_end`が最大の書類の定性情報を返す
- `period_end`指定時：一致する`period_end`の書類の定性情報を返す（一致する書類が
  ない場合は`404`）
- レスポンスには、年度セレクタの選択肢を組み立てるための`available_periods`
  （定性情報が存在する書類の`period_end`一覧、降順）を含める
- レスポンス例：
  ```json
  {
    "period_end": "2026-04-30",
    "available_periods": ["2026-04-30", "2025-04-30", "2024-04-30"],
    "business_description": "３【事業の内容】...",
    "business_risks": "３【事業等のリスク】...",
    "mdanda": "４【経営者による財政状態...】..."
  }
  ```
  `business_description`・`business_risks`・`mdanda`は、該当するテキストブロックが
  存在しない場合`null`
- 対象企業の書類が1件もない場合は`404`（既存のAPI-COM-002等と同じエラー方針）

`backend/schemas.py`に`CompanyQualitativeFacts`スキーマを追加し、
`backend/routers/companies.py`（既存のAPI-COM系ルーター）にエンドポイントを追加する。

---

## 4. バッチの整理

### FR-59：既存`facts`テーブル・関連コードの命名是正

`facts`（定量データ）・新設する定性データテーブルの両方が「名前から中身が
読み取れない」曖昧な命名だったため、対になる名前に是正する
（`docs/requirements/cycle13_requirements.md` FR-59の対応表参照）。

#### `backend/database.py`：`Fact`→`CompanyQuantitativeFact`、新規`CompanyQualitativeFact`

```python
class CompanyQuantitativeFact(Base):
    """company_quantitative_facts（旧facts、サイクル13でリネーム）

    EDINETのXBRL数値データを要素単位で汎用的に保持する（企業の定量データ）。
    """

    __tablename__ = "company_quantitative_facts"
    # カラム定義は旧Factクラスと同一（変更なし）。テーブル名・クラス名のみ変更


class Document(Base):
    """documents（変更なし。facts_ingested_at→body_ingested_atのみリネーム）"""

    # ...既存のカラムはそのまま。以下のみ変更：
    body_ingested_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    # 旧名 facts_ingested_at。この書類の本体（企業の定量データ・定性データ双方）を
    # 取り込み済みかを表すため、特定のテーブル名を含まない名前にリネームした


class CompanyQualitativeFact(Base):
    """company_qualitative_facts（TBL-005、サイクル13新設）

    company_quantitative_factsが数値データを持つのに対し、こちらは事業の内容・
    リスク・MD&Aのテキストブロックを保持する（企業の定性データ）。
    """

    __tablename__ = "company_qualitative_facts"
    __table_args__ = (
        Index("idx_company_qualitative_facts_company_period", "company_code", "period_end"),
    )

    doc_id: Mapped[str] = mapped_column(
        String(8), ForeignKey("documents.doc_id", ondelete="CASCADE"), primary_key=True
    )
    element_id: Mapped[str] = mapped_column(String(100), primary_key=True)
    company_code: Mapped[str] = mapped_column(
        String(10), ForeignKey("companies.code", ondelete="CASCADE"), nullable=False
    )
    period_end: Mapped[date | None] = mapped_column(Date, nullable=True)
    content: Mapped[str] = mapped_column(Text, nullable=False)
```

`element_id`は3値（`jpcrp_cor:DescriptionOfBusinessTextBlock`・
`jpcrp_cor:BusinessRisksTextBlock`・
`jpcrp_cor:ManagementAnalysisOfFinancialPositionOperatingResultsAndCashFlowsTextBlock`）
のいずれか。複合主キー`(doc_id, element_id)`で1書類につき最大3行。

#### Alembicマイグレーション

1件目（リネーム。テーブル名・`documents`のカラム名の両方）：
```python
def upgrade() -> None:
    op.execute("ALTER TABLE facts RENAME TO company_quantitative_facts")
    op.execute("ALTER TABLE documents RENAME COLUMN facts_ingested_at TO body_ingested_at")


def downgrade() -> None:
    op.execute("ALTER TABLE documents RENAME COLUMN body_ingested_at TO facts_ingested_at")
    op.execute("ALTER TABLE company_quantitative_facts RENAME TO facts")
```

SQLite 3.25以降は`RENAME COLUMN`に対応済み（プロジェクトのSQLiteバージョンで
動作確認する）。

2件目（新設）：`company_qualitative_facts`テーブルとインデックスを作成する
（`documents`テーブルの作成マイグレーションと同じ形式）。

### `backend/xbrl_parser.py`：命名是正＋定性データ抽出関数の新設

```python
# 旧NumericFact → QuantitativeFact（リネーム）
@dataclass
class QuantitativeFact:
    element_id: str
    element_name: str | None
    context_id: str
    consolidated_or_individual: str | None
    period_or_instant: str | None
    unit: str | None
    value: Decimal


# 旧parse_numeric_facts → parse_quantitative_facts（リネーム、ロジック変更なし）
def parse_quantitative_facts(csv_bytes: bytes) -> list[QuantitativeFact]:
    ...


TARGET_QUALITATIVE_ELEMENT_IDS = {
    "jpcrp_cor:DescriptionOfBusinessTextBlock",
    "jpcrp_cor:BusinessRisksTextBlock",
    "jpcrp_cor:ManagementAnalysisOfFinancialPositionOperatingResultsAndCashFlowsTextBlock",
}


@dataclass
class QualitativeFact:
    element_id: str
    content: str


def parse_qualitative_facts(csv_bytes: bytes) -> list[QualitativeFact]:
    """提出本文書CSVから対象の定性データテキストブロックを抽出する（サイクル13 FR-58）"""
    reader = _read_csv_rows(csv_bytes)
    blocks: dict[str, QualitativeFact] = {}
    for row in reader:
        if row["単位"] != _TEXT_BLOCK_UNIT:
            continue
        if row["要素ID"] not in TARGET_QUALITATIVE_ELEMENT_IDS:
            continue
        if not row["値"].strip():
            continue
        blocks.setdefault(row["要素ID"], QualitativeFact(element_id=row["要素ID"], content=row["値"]))
    return list(blocks.values())
```

`parse_quantitative_facts`と同じCSVを2回パースする形になるが、CSV自体は既に
メモリ上にある（再取得ではない）ため許容する。

### `backend/fact_ingestion.py` → `backend/quantitative_fact_ingestion.py`（リネーム）＋定性データupsert関数

ファイル名を`quantitative_fact_ingestion.py`にリネームする。既存の
`upsert_company`・`upsert_facts`（→`upsert_quantitative_facts`にリネーム、
ロジック変更なし）に加え、新規関数を追加する：

```python
def upsert_qualitative_facts(
    session, company_code: str, doc_id: str, period_end: date | None, qualitative_facts: list[xbrl_parser.QualitativeFact]
) -> None:
    for fact in qualitative_facts:
        record = session.get(CompanyQualitativeFact, (doc_id, fact.element_id))
        if record is None:
            record = CompanyQualitativeFact(doc_id=doc_id, element_id=fact.element_id)
            session.add(record)
        record.company_code = company_code
        record.period_end = period_end
        record.content = fact.content
```

### `backend/document_body_ingestion.py`の拡張

`ingest_document_body`内、`company_quantitative_facts`保存と同じタイミングで
`parse_qualitative_facts`・`upsert_qualitative_facts`を呼ぶ（同じ`csv_bytes`を
再利用、追加のEDINET通信なし）。

### 呼び出し元の追随（FR-59）

- `backend/routers/edinet.py`：`from quantitative_fact_ingestion import upsert_company,
  upsert_quantitative_facts`に変更、呼び出し箇所も追随
- `backend/scripts/ingest_document_bodies.py`：インポート元の変更、
  `Document.facts_ingested_at`→`Document.body_ingested_at`に追随
- `backend/document_list_ingestion.py`・`backend/scripts/ingest_document_list_backfill.py`：
  `facts_ingested_at`への言及があれば`body_ingested_at`に追随（実装時に`grep`で確認）

### FR-60：個別ダウンロード機能（SCR-001）とdocumentsテーブルの不整合是正

BATCH-005の対象件数を確認する過程で発見（詳細：`cycle13_requirements.md` FR-60）。
`routers/edinet.py`の`run_download_job`（個別ダウンロード、サイクル9より前から
存在）は`documents`テーブルを一切更新していなかった。`document_list_ingestion.py`
から書類1件分のupsertロジックを`upsert_document_from_row`として切り出し、
`run_download_job`でも使うようにする：

```python
# document_list_ingestion.py
def upsert_document_from_row(session, company_code: str, list_date: date, row: dict) -> Document:
    document = session.get(Document, row["docID"])
    if document is None:
        document = Document(doc_id=row["docID"])
        session.add(document)
    document.edinet_code = row["edinetCode"]
    document.company_code = company_code
    document.doc_type_code = row["docTypeCode"]
    document.period_start = date.fromisoformat(row["periodStart"]) if row.get("periodStart") else None
    document.period_end = date.fromisoformat(row["periodEnd"]) if row.get("periodEnd") else None
    document.submit_date_time = row["submitDateTime"]
    document.list_date = list_date
    document.withdrawal_status = row.get("withdrawalStatus")
    document.disclosure_status = row.get("disclosureStatus")
    document.csv_flag = row.get("csvFlag")
    return document
```

`routers/edinet.py`の`run_download_job`は、`search_report`が返す`document`
（書類一覧APIと同じ形状の辞書）を使ってこの関数を呼び、あわせて定性データも
保存し、`body_ingested_at`を設定する：

```python
quantitative_facts = xbrl_parser.parse_quantitative_facts(csv_bytes)
upsert_quantitative_facts(session, company_code, document["docID"], document["docTypeCode"], expected_period_end, quantitative_facts)

# list_dateはsearch_reportが検索に使った日付を返さないため、submitDateTimeの
# 日付部分で代用する（進捗管理用の参考値であり、正確な一致は必須ではない）
list_date = date.fromisoformat(document["submitDateTime"][:10])
document_row = upsert_document_from_row(session, company_code, list_date, document)

qualitative_facts = xbrl_parser.parse_qualitative_facts(csv_bytes)
upsert_qualitative_facts(session, company_code, document["docID"], expected_period_end, qualitative_facts)

document_row.body_ingested_at = datetime.now()
session.commit()
```

実機検証（会社コード1376、未ダウンロード企業）：ダウンロード実行後、
`documents`にレコードが作成され`body_ingested_at`が設定され、
`company_qualitative_facts`にも正しく保存されることを確認した。

### 新規バッチ：`backend/scripts/backfill_qualitative_facts.py`（BATCH-005）

`company_quantitative_facts`に定量データが存在する書類（515件）のうち、
`documents.body_ingested_at`が未設定の書類（FR-60の不整合により485件）を
対象に、CSVを再取得して`company_qualitative_facts`を追加し、
`documents.body_ingested_at`も設定する遡及バッチ（ユーザー許可済み、約485
リクエスト・約5分規模）。`company_quantitative_facts`自体は変更しない。

```python
def main() -> None:
    with SessionLocal() as session:
        target_doc_ids = [d for (d,) in session.query(CompanyQuantitativeFact.doc_id).distinct().all()]
        documents = session.query(Document).filter(
            Document.doc_id.in_(target_doc_ids), Document.body_ingested_at.is_(None)
        ).all()
        for document in documents:
            csv_bytes = edinet_client.fetch_report_csv(document.doc_id, document.doc_type_code)
            qualitative_facts = xbrl_parser.parse_qualitative_facts(csv_bytes)
            upsert_qualitative_facts(session, document.company_code, document.doc_id, document.period_end, qualitative_facts)
            document.body_ingested_at = datetime.now()
            session.commit()
```

---

## 5. DBスキーマ変更に伴う必須更新（cycle-workflow参照）

- `docs/design/table/TBL-003_facts.md` → `TBL-003_company_quantitative_facts.md`
  にリネーム・内容更新（テーブル名の変更を反映）
- `docs/design/table/TBL-005_company_qualitative_facts.md`（新規）
- `docs/design/table/er_diagram.md`（`company_quantitative_facts`・
  `company_qualitative_facts`に更新）
- `docs/design/table/table_list.md`（`TBL-003`・`TBL-005`を更新）

## 6. バッチ追加に伴う必須更新

- `docs/design/batch/BATCH-005_backfill_qualitative_facts.md`（新規）
- `docs/design/batch/batch_list.md`（`BATCH-005`追記）
- 既存`BATCH-001`〜`004`の定義書内で`facts`に言及している箇所があれば
  `company_quantitative_facts`に更新する

---

## 7. 変更ファイル一覧

| ファイル | 変更内容 | 関連FR |
|---|---|---|
| `docs/design/screen/items/SCR-003_items.md` | 実装に合わせて全面更新（対応済み） | FR-57 |
| `backend/database.py` | `Fact`→`CompanyQuantitativeFact`リネーム、`Document.facts_ingested_at`→`body_ingested_at`リネーム、`CompanyQualitativeFact`追加 | FR-58, FR-59 |
| `backend/alembic/versions/<new1>.py` | `facts`→`company_quantitative_facts`リネームマイグレーション | FR-59 |
| `backend/alembic/versions/<new2>.py` | `company_qualitative_facts`テーブル作成マイグレーション | FR-58 |
| `backend/xbrl_parser.py` | `parse_numeric_facts`→`parse_quantitative_facts`等リネーム、`parse_qualitative_facts`・`QualitativeFact`追加 | FR-58, FR-59 |
| `backend/fact_ingestion.py` | `quantitative_fact_ingestion.py`にリネーム、`upsert_qualitative_facts`追加 | FR-58, FR-59 |
| `backend/document_body_ingestion.py` | インポート元変更、定性データ保存呼び出し追加 | FR-58, FR-59 |
| `backend/routers/edinet.py` | インポート元変更、`upsert_document_from_row`呼び出し・定性データ保存・`body_ingested_at`設定を追加 | FR-59, FR-60 |
| `backend/scripts/ingest_document_bodies.py` | インポート元変更、`body_ingested_at`に追随 | FR-59 |
| `backend/document_list_ingestion.py` | `upsert_document_from_row`を切り出し（`run_download_job`と共用） | FR-60 |
| `docs/design/table/TBL-004_documents.md` | `facts_ingested_at`→`body_ingested_at`に更新 | FR-59 |
| `backend/scripts/backfill_qualitative_facts.py` | 新規（遡及バッチ、BATCH-005。対象を`company_quantitative_facts`基準に修正、`body_ingested_at`設定も追加） | FR-58, FR-60 |
| `backend/schemas.py` | `CompanyQualitativeFacts`スキーマ追加、`FactRecord`はSCR-004削除に伴い削除済み | FR-58, FR-59 |
| `backend/routers/companies.py` | `API-COM-006`エンドポイント追加、`facts`→`quantitative_facts`変数名リネーム、SCR-004削除に伴い`API-COM-004`エンドポイント削除 | FR-58, FR-59 |
| `frontend/src/components/QualitativeFactSection.tsx` | 新規（開閉式表示コンポーネント、句点改行対応） | FR-58 |
| `frontend/src/pages/CompanyDetailPage.tsx` | 「事業概要・リスク」セクション追加（常時表示、独立年度セレクタ） | FR-58 |
| `frontend/src/api/client.ts` | `getCompanyQualitativeFacts`追加、SCR-004削除に伴い`getCompanyFacts`系を削除 | FR-58, FR-59 |
| `docs/design/table/TBL-003_company_quantitative_facts.md` | リネーム・更新 | FR-59 |
| `docs/design/table/TBL-005_company_qualitative_facts.md` | 新規 | FR-58 |
| `docs/design/table/er_diagram.md` | 更新 | FR-58, FR-59 |
| `docs/design/table/table_list.md` | 更新 | FR-58, FR-59 |
| `docs/design/batch/BATCH-005_backfill_qualitative_facts.md` | 新規 | FR-58, FR-60 |
| （削除）`frontend/src/pages/CompanyQuantitativeFactsPage.tsx`（旧`CompanyFactsPage.tsx`） | SCR-004削除（ユースケースに紐づかない開発者向け機能と判断） | ユーザー指示 |
| （削除）`docs/design/screen/SCR-004_facts_browser.md`・`items/SCR-004_items.md` | 同上 | ユーザー指示 |
| （削除）`docs/design/api/paths/com/companies_code_facts.yaml`・`components/schemas/FactRecord.yaml` | 同上 | ユーザー指示 |
| `docs/design/batch/batch_list.md` | `BATCH-005`追記 | FR-58 |
| `docs/design/api/api_list.md` | `API-COM-006`追記 | FR-58 |

---

## 8. 動作確認方針

- リネーム後、既存の個別ダウンロード機能（`POST /api/download`）・
  `GET /api/companies`等が引き続き正常動作することを確認する（テーブル名変更の
  回帰確認）
- 会社コード5971（実データ検証済み）で
  `GET /api/companies/5971/qualitative-facts`（`period_end`省略時＝最新、
  `period_end`指定時）の両方が正しい定性情報を返すことを確認する。複数年度の
  書類を持つ企業で`available_periods`が複数年度分返ることも確認する
- フロントエンドでSCR-003を開き、B/S・P/L・CF・財務分析指標（既存機能の回帰なし）・
  定性情報セクション（年度セレクタでの切り替え・開閉動作含む）を目視確認する
- `backfill_qualitative_facts.py`実行後、`company_qualitative_facts`テーブルの
  行数・内容を確認する（実行前にユーザーへ最終確認：約515リクエスト規模の実行）
