"""全上場企業の基本情報をcompaniesテーブルに一括登録する（サイクル6 FR-39）。

実行方法：backend/ディレクトリで `python -m scripts.bulk_register_companies`
1回限りの手動実行想定。再実行しても同じ結果になる（冪等）。
"""
import logging

from database import Company, SessionLocal
from edinet_client import list_all_filers, to_company_code

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)


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
                code = to_company_code(filer.sec_code)
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
