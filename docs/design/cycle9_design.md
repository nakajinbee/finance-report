# サイクル9 設計書

対象：[cycle9_requirements.md](../requirements/cycle9_requirements.md) FR-48〜51

実装順：FR-48（テーブル定義・マイグレーション）→ FR-49（書類一覧の取り込み、実データで
過去10年分を実行）→ FR-50（書類本体の取り込み、少数サンプルで動作確認）→
FR-51（ドキュメント整合性確認）

---

## 1. FR-48：`TBL-004 documents`の新設

### `backend/database.py`

```diff
+ from datetime import date, datetime
- from datetime import date
  from decimal import Decimal
  ...
  from sqlalchemy import (
      Date,
+     DateTime,
      ForeignKey,
      Index,
      Numeric,
      String,
      UniqueConstraint,
      create_engine,
  )
```

```python
class Document(Base):
    """TBL-004 documents（書類一覧APIのメタデータ）

    facts（数値データそのもの）とは別に「どの書類が存在するか」の索引を持つ。
    company_code・sec_codeを持たない書類（ファンド等）や、対象外の書類種別
    （有価証券報告書・半期報告書以外）は保存しない（サイクル9 FR-48）。
    """

    __tablename__ = "documents"
    __table_args__ = (
        Index("idx_documents_company_ingested", "company_code", "facts_ingested_at"),
        Index("idx_documents_list_date", "list_date"),
    )

    doc_id: Mapped[str] = mapped_column(String(8), primary_key=True)
    edinet_code: Mapped[str] = mapped_column(String(10), nullable=False)
    company_code: Mapped[str] = mapped_column(
        String(10), ForeignKey("companies.code", ondelete="CASCADE"), nullable=False
    )
    doc_type_code: Mapped[str] = mapped_column(String(3), nullable=False)
    period_start: Mapped[date | None] = mapped_column(Date, nullable=True)
    period_end: Mapped[date | None] = mapped_column(Date, nullable=True)
    submit_date_time: Mapped[str] = mapped_column(String(16), nullable=False)
    list_date: Mapped[date] = mapped_column(Date, nullable=False)
    withdrawal_status: Mapped[str | None] = mapped_column(String(1), nullable=True)
    disclosure_status: Mapped[str | None] = mapped_column(String(1), nullable=True)
    csv_flag: Mapped[str | None] = mapped_column(String(1), nullable=True)
    facts_ingested_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
```

**設計判断のポイント**：

- `doc_id`をそのまま主キーにする（`companies.code`と同じ流儀。EDINETの書類管理番号は
  グローバルに一意なため、独自の連番`id`は不要）
- `company_code`は`NOT NULL`にする：`sec_code`変換に失敗した書類・`companies`に
  存在しない書類は、そもそも本テーブルに保存しない（要件定義FR-49の追記事項の通り、
  スキップしてログに残すのみ）。中途半端に`company_code=NULL`の行を残さないことで、
  「保存されている＝解析済みの正規の書類」という不変条件を保てる
- `submit_date_time`はEDINETのレスポンス形式（`YYYY-MM-DD hh:mm`文字列）をそのまま
  `String`で保持する（`date_format_policy.md`：日時が必要な値で、既存の`period_end`
  （`Date`型）と混同しない。実際の並び替え等が必要になった場合は設計を見直す）
- `facts_ingested_at`は`datetime.datetime | None`（`DateTime`カラム）。
  `document_body_ingestion.py`で`datetime.now()`をそのまま代入する

### Alembicマイグレーション（新規）

```python
def upgrade() -> None:
    op.execute(
        """
        CREATE TABLE documents (
            doc_id VARCHAR(8) PRIMARY KEY NOT NULL,
            edinet_code VARCHAR(10) NOT NULL,
            company_code VARCHAR(10) NOT NULL,
            doc_type_code VARCHAR(3) NOT NULL,
            period_start DATE,
            period_end DATE,
            submit_date_time VARCHAR(16) NOT NULL,
            list_date DATE NOT NULL,
            withdrawal_status VARCHAR(1),
            disclosure_status VARCHAR(1),
            csv_flag VARCHAR(1),
            facts_ingested_at DATETIME,
            CONSTRAINT fk_documents_company FOREIGN KEY (company_code)
                REFERENCES companies (code) ON DELETE CASCADE
        )
        """
    )
    op.execute("CREATE INDEX idx_documents_company_ingested ON documents (company_code, facts_ingested_at)")
    op.execute("CREATE INDEX idx_documents_list_date ON documents (list_date)")


def downgrade() -> None:
    op.execute("DROP TABLE documents")
```

---

## 2. FR-49：書類一覧の取り込み処理（日付ポーリング）

### `backend/fact_ingestion.py`（新規、`_upsert_company`・`_upsert_facts`の移設先）

`routers/edinet.py`にある`_upsert_company`・`_upsert_facts`は、FR-50でも同じロジックが
必要になるため、共通モジュールに切り出す（重複させない）。ロジック自体は変更しない。

```python
"""companies・factsテーブルへの書き込みロジック（routers/edinet.pyとscripts/両方から使う）"""
from datetime import date

from database import Company, Fact
import xbrl_parser


def upsert_company(session, company_code: str, name: str, sector: str | None, accounting_standard: str) -> None:
    company = session.get(Company, company_code)
    if company is None:
        company = Company(code=company_code)
        session.add(company)
    company.name = name
    company.sector = sector
    company.accounting_standard = accounting_standard


def upsert_facts(
    session, company_code: str, doc_id: str, doc_type_code: str, period_end: date, facts: list[xbrl_parser.NumericFact]
) -> None:
    """CSVから抽出した数値データ(NumericFact)をすべてTBL-003 factsへ保存する（FR-04）"""
    for numeric_fact in facts:
        fact = (
            session.query(Fact)
            .filter_by(
                company_code=company_code,
                doc_id=doc_id,
                element_id=numeric_fact.element_id,
                context_id=numeric_fact.context_id,
            )
            .one_or_none()
        )
        if fact is None:
            fact = Fact(
                company_code=company_code,
                doc_id=doc_id,
                element_id=numeric_fact.element_id,
                context_id=numeric_fact.context_id,
            )
            session.add(fact)
        fact.doc_type_code = doc_type_code
        fact.period_end = period_end
        fact.element_name = numeric_fact.element_name
        fact.consolidated_or_individual = numeric_fact.consolidated_or_individual
        fact.period_or_instant = numeric_fact.period_or_instant
        fact.unit = numeric_fact.unit
        fact.value = numeric_fact.value
```

`routers/edinet.py`側は`from fact_ingestion import upsert_company, upsert_facts`に変更し、
ローカル定義の`_upsert_company`・`_upsert_facts`を削除する。呼び出し箇所
（`_upsert_company(...)`→`upsert_company(...)`）もあわせて変更するが、渡す引数・
ロジックは一切変えない（純粋なリファクタリング）。

### `backend/document_list_ingestion.py`（新規）

```python
"""書類一覧APIの結果をdocumentsテーブルへ取り込む（サイクル9 FR-49）"""
import logging
from datetime import date, timedelta

import edinet_client
from database import Company, Document, SessionLocal

logger = logging.getLogger(__name__)

TARGET_DOC_TYPE_CODES = {
    edinet_client.DOC_TYPE_CODE_ANNUAL_REPORT,
    edinet_client.DOC_TYPE_CODE_SEMI_ANNUAL_REPORT,
}


def ingest_document_list_for_date(session, target_date: date) -> dict[str, int]:
    """指定日の書類一覧を取得し、対象書類をdocumentsへupsertする。件数の内訳を返す。"""
    counts = {"stored": 0, "skipped_doctype_or_no_seccode": 0, "skipped_conversion": 0, "skipped_no_company": 0}

    for row in edinet_client.fetch_document_list(target_date):
        if row.get("secCode") is None or row.get("docTypeCode") not in TARGET_DOC_TYPE_CODES:
            counts["skipped_doctype_or_no_seccode"] += 1
            continue

        try:
            company_code = edinet_client.to_company_code(row["secCode"])
        except ValueError:
            logger.warning("証券コードの変換に失敗: doc_id=%s secCode=%s", row["docID"], row["secCode"])
            counts["skipped_conversion"] += 1
            continue

        if session.get(Company, company_code) is None:
            counts["skipped_no_company"] += 1
            continue

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
        document.list_date = target_date
        document.withdrawal_status = row.get("withdrawalStatus")
        document.disclosure_status = row.get("disclosureStatus")
        document.csv_flag = row.get("csvFlag")
        counts["stored"] += 1

    session.commit()
    return counts
```

### `backend/scripts/ingest_document_list_backfill.py`（新規）

```python
"""過去BACKFILL_YEARS年分の書類一覧を、今日から1日ずつ遡って取り込む（サイクル9 FR-49）。

実行方法：backend/ディレクトリで `python -m scripts.ingest_document_list_backfill`
"""
import logging
from datetime import date, timedelta

from database import SessionLocal
from document_list_ingestion import ingest_document_list_for_date

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

BACKFILL_YEARS = 10


def main() -> None:
    today = date.today()
    total = {"stored": 0, "skipped_doctype_or_no_seccode": 0, "skipped_conversion": 0, "skipped_no_company": 0}

    with SessionLocal() as session:
        for offset in range((BACKFILL_YEARS * 365) + 1):
            target_date = today - timedelta(days=offset)
            counts = ingest_document_list_for_date(session, target_date)
            for key in total:
                total[key] += counts[key]
            if offset % 100 == 0:
                logger.info("進捗: %s まで処理, 累計stored=%d", target_date, total["stored"])

    logger.info("完了: %s", total)


if __name__ == "__main__":
    main()
```

**設計判断のポイント**：

- `ingest_document_list_for_date`は「1日分の取り込み」を担う独立関数にし、初回の
  過去10年分バックフィル（`ingest_document_list_backfill.py`）にも、将来の日次実行
  （1日分だけ呼ぶ）にも同じ関数を使う（要件定義の狙い通り）
- `session.get(Document, row["docID"])`による存在チェック＋更新で、同じ`doc_id`を
  再取得しても内容を最新化するだけで重複行は作らない（冪等）
- 進捗ログは100日ごとに出す（約3,650回のループ全部をログに残すと出力過多になるため）

**実装中に追加した変更（実データでの実行中に通信の瞬断で停止したため）**：

- `backend/edinet_client.py`の`_get`に、`ConnectionError`/`Timeout`発生時のリトライ
  （最大3回、5秒間隔）を追加した。長時間のバッチ処理が通信の一時的な瞬断1回で
  全体停止しないようにするため。既存の呼び出し元（`routers/edinet.py`等）への
  影響はない（`_get`の戻り値・例外の意味は変えず、リトライで吸収できなかった場合のみ
  従来通り例外を送出する）
- `ingest_document_list_backfill.py`に再開機能を追加した。`documents`テーブルに
  記録済みの最も古い`list_date`があれば、その1日前から処理を再開する
  （今日からやり直さず、既に取得済みの日付への再アクセスを避ける）

---

## 3. FR-50：書類本体の取り込み処理（CSV取得・facts保存）

### `backend/document_body_ingestion.py`（新規）

```python
"""documentsテーブルの未取得書類を対象に、CSVを取得しfactsへ保存する（サイクル9 FR-50）"""
import logging
from datetime import datetime

import edinet_client
import xbrl_parser
from database import Company, Document
from fact_ingestion import upsert_company, upsert_facts

logger = logging.getLogger(__name__)

WITHDRAWN_STATUSES = {"1", "2"}  # EDINET_API_仕様書.pdf 3-1-2-2 No.32「取下区分」


def ingest_document_body(session, document: Document) -> bool:
    """1件の書類本体を取得・パースしfactsへ保存する。成功したらTrueを返す。"""
    if document.csv_flag != "1" or document.withdrawal_status in WITHDRAWN_STATUSES:
        return False

    try:
        csv_bytes = edinet_client.fetch_report_csv(document.doc_id, document.doc_type_code)
        company = session.get(Company, document.company_code)
        if company.accounting_standard is None:
            accounting_standard = xbrl_parser.extract_accounting_standard(csv_bytes)
            upsert_company(session, company.code, company.name, company.sector, accounting_standard)

        facts = xbrl_parser.parse_numeric_facts(csv_bytes)
        upsert_facts(session, document.company_code, document.doc_id, document.doc_type_code, document.period_end, facts)
        document.facts_ingested_at = datetime.now()
        session.commit()
        return True
    except Exception:
        session.rollback()
        logger.exception("書類本体の取り込みに失敗: doc_id=%s", document.doc_id)
        return False
```

### `backend/scripts/ingest_document_bodies.py`（新規）

```python
"""documentsの未取得書類を対象にingest_document_bodyを実行する（サイクル9 FR-50）。

実行方法：backend/ディレクトリで `python -m scripts.ingest_document_bodies`
SAMPLE_LIMITを指定すると件数を絞れる（本サイクルは少数サンプルでの動作確認が目的のため、
デフォルトで件数を絞る。全件実行する場合はNoneに変更する）。
"""
import logging

from database import Document, SessionLocal
from document_body_ingestion import ingest_document_body

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

SAMPLE_LIMIT: int | None = 30


def main() -> None:
    succeeded = 0
    failed = 0

    with SessionLocal() as session:
        query = session.query(Document).filter(Document.facts_ingested_at.is_(None), Document.csv_flag == "1")
        if SAMPLE_LIMIT is not None:
            query = query.limit(SAMPLE_LIMIT)
        documents = query.all()

        for document in documents:
            if ingest_document_body(session, document):
                succeeded += 1
            else:
                failed += 1

    logger.info("完了: 成功=%d件, 失敗/スキップ=%d件", succeeded, failed)


if __name__ == "__main__":
    main()
```

---

## 4. FR-51：既存テーブル・画面との整合性確認

- `docs/design/table/TBL-004_documents.md`を新設する（`TBL-001`〜`TBL-003`と同じ
  形式のテーブル定義書：カラム定義・インデックス・外部キー制約・備考）
- `docs/design/table/er_diagram.md`に`documents`テーブルを追加し、`companies`との
  1対多関係（`documents.company_code` → `companies.code`）を明記する。`facts`とは
  直接の外部キー関係を持たない（`doc_id`は両方に存在するが、片方からもう片方を
  正式に参照する制約は設けない。将来必要になれば別途検討）
- `docs/design/table/table_list.md`に`TBL-004 documents`を追記する
- `routers/edinet.py`の個別ダウンロード機能は、リファクタリング（`upsert_company`・
  `upsert_facts`の呼び出し元変更のみ）以外の変更をしない。実装後、実際に
  `POST /api/download`を1社分実行し、既存の動作が壊れていないことを確認する
- `GET /api/companies`等の既存APIは今回変更しない。`documents`テーブルの存在は
  レスポンスに影響しない

---

## 5. 変更ファイル一覧

| ファイル | 変更内容 | 関連FR |
|---|---|---|
| `backend/database.py` | `Document`モデル追加 | FR-48 |
| `backend/alembic/versions/<new>.py` | `documents`テーブル作成マイグレーション | FR-48 |
| `backend/fact_ingestion.py` | 新規（`upsert_company`・`upsert_facts`を`routers/edinet.py`から移設） | FR-49, FR-50 |
| `backend/routers/edinet.py` | ローカル定義削除、`fact_ingestion`からimportに変更 | FR-49, FR-50 |
| `backend/document_list_ingestion.py` | 新規（1日分の書類一覧取り込み） | FR-49 |
| `backend/scripts/ingest_document_list_backfill.py` | 新規（過去10年分の実行） | FR-49 |
| `backend/document_body_ingestion.py` | 新規（1件の書類本体取り込み） | FR-50 |
| `backend/scripts/ingest_document_bodies.py` | 新規（未取得書類のサンプル実行） | FR-50 |
| `docs/design/table/TBL-004_documents.md` | 新規（テーブル定義書） | FR-51 |
| `docs/design/table/er_diagram.md` | `documents`追加 | FR-51 |
| `docs/design/table/table_list.md` | `TBL-004`追記 | FR-51 |

---

## 6. 動作確認方針

- `ingest_document_list_backfill.py`を実際に実行し、過去10年分（約3,650日）の
  書類一覧を取り込む（実データ、モックなし）。所要時間・取り込み件数を記録する
- `ingest_document_bodies.py`を実行し、`SAMPLE_LIMIT=30`件程度で書類本体の取得・
  `facts`保存が正しく行われることを確認する
- リファクタリング後、既存の個別ダウンロード機能（`POST /api/download`）を1社分実行し、
  壊れていないことを確認する
- `GET /api/companies`が引き続き正常応答することを確認する
