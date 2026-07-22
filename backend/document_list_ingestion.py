"""書類一覧APIの結果をdocumentsテーブルへ取り込む（サイクル9 FR-49）。

EDINETの書類一覧APIは日付を指定してその日の全提出書類を返す設計であり、企業を指定して
取得する機能はない。この設計に沿い、1日分の取り込みを担う関数を独立させ、過去に遡る
初回一括投入（scripts/ingest_document_list_backfill.py）にも、将来の日次実行にも
同じ関数を使えるようにする。
"""
import logging
from datetime import date

import edinet_client
from database import Company, Document

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
