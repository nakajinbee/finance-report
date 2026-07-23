"""既にcompany_quantitative_factsへ定量データが取り込み済みの書類を対象に、CSVを
再取得してcompany_qualitative_factsを追加保存する遡及バッチ（BATCH-005、サイクル13 FR-58）。

対象は「company_quantitative_factsに存在する書類（distinct doc_id）のうち、
documents.body_ingested_atが未設定のもの」。company_quantitative_factsは合計515件
存在するが、サイクル9のFR-50サンプル30件＋個別ダウンロードで確認用に取得した数件は
既にbody_ingested_atが設定済み・定性データも取得済みのため対象から自然に除外される。

判明した経緯（サイクル13 UC-1-1実装中）：個別ダウンロード機能
（routers/edinet.py、SCR-001）は長年documentsテーブルを更新しておらず、
定量データはcompany_quantitative_factsにあるのにbody_ingested_atが未設定という
ズレが485件分蓄積していた。この不整合はrouters/edinet.py側を修正して解消したが
（FR-59）、既に取り込み済みの過去分については本バッチで定性データを補い、
documents.body_ingested_atも設定して以後の整合性を保つ。

company_quantitative_facts自体は変更しない。ユーザーの事前許可済み
（約515回のEDINETリクエスト・約5分規模、2026-07-23）。

実行方法：backend/ディレクトリで `python -m scripts.backfill_qualitative_facts`
"""
import logging
from datetime import datetime

import edinet_client
import xbrl_parser
from database import CompanyQuantitativeFact, Document, SessionLocal
from quantitative_fact_ingestion import upsert_qualitative_facts

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)


def main() -> None:
    succeeded = 0
    failed = 0

    with SessionLocal() as session:
        target_doc_ids = [
            doc_id
            for (doc_id,) in session.query(CompanyQuantitativeFact.doc_id).distinct().all()
        ]
        documents = (
            session.query(Document)
            .filter(Document.doc_id.in_(target_doc_ids), Document.body_ingested_at.is_(None))
            .all()
        )
        logger.info("対象書類数: %d件（company_quantitative_facts総数: %d件）", len(documents), len(target_doc_ids))

        for i, document in enumerate(documents, start=1):
            try:
                csv_bytes = edinet_client.fetch_report_csv(document.doc_id, document.doc_type_code)
                qualitative_facts = xbrl_parser.parse_qualitative_facts(csv_bytes)
                upsert_qualitative_facts(
                    session, document.company_code, document.doc_id, document.period_end, qualitative_facts
                )
                document.body_ingested_at = datetime.now()
                session.commit()
                succeeded += 1
            except Exception:
                session.rollback()
                logger.exception("定性データの遡及取得に失敗: doc_id=%s", document.doc_id)
                failed += 1

            if i % 50 == 0:
                logger.info("進捗: %d/%d件処理済み", i, len(documents))

    logger.info("完了: 成功=%d件, 失敗=%d件", succeeded, failed)


if __name__ == "__main__":
    main()
