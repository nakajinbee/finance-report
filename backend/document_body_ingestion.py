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
