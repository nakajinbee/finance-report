"""過去BACKFILL_YEARS年分の書類一覧を、今日から1日ずつ遡って取り込む（サイクル9 FR-49）。

実行方法：backend/ディレクトリで `python -m scripts.ingest_document_list_backfill`

途中で（通信の瞬断等により）停止した場合、再実行するとdocumentsテーブルに記録済みの
最も古いlist_dateの1日前から再開する（今日からやり直さない。既に取得済みの日付への
再アクセスを避けるため）。
"""
import logging
from datetime import date, timedelta

from database import Document, SessionLocal
from document_list_ingestion import ingest_document_list_for_date

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

BACKFILL_YEARS = 10


def main() -> None:
    today = date.today()
    end_date = today - timedelta(days=BACKFILL_YEARS * 365)
    total = {"stored": 0, "skipped_doctype_or_no_seccode": 0, "skipped_conversion": 0, "skipped_no_company": 0}

    with SessionLocal() as session:
        oldest_recorded = session.query(Document.list_date).order_by(Document.list_date.asc()).first()
        if oldest_recorded is not None:
            start_date = oldest_recorded[0] - timedelta(days=1)
            logger.info("再開: %s から処理を続行します（前回記録済みの最古日付の1日前）", start_date)
        else:
            start_date = today

        target_date = start_date
        while target_date >= end_date:
            counts = ingest_document_list_for_date(session, target_date)
            for key in total:
                total[key] += counts[key]
            if (start_date - target_date).days % 100 == 0:
                logger.info("進捗: %s まで処理, 今回分stored=%d", target_date, total["stored"])
            target_date -= timedelta(days=1)

    logger.info("完了: %s", total)


if __name__ == "__main__":
    main()
