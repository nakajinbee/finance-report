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
