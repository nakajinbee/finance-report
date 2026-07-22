"""少数企業でバッチ取得の所要時間・EDINETリクエスト回数を実測する
(サイクル7 FR-43、IDEA-01フェーズ2)。

実行方法：backend/ディレクトリで `python -m scripts.verify_batch_timing`
"""
import logging
import time

import edinet_client
import schemas
from database import Company, SessionLocal
from routers.edinet import _states, run_download_job

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

SAMPLE_SECTOR_LIMIT = 20


def select_sample_companies(session) -> list[Company]:
    """業種ごとに1社（code昇順で先頭）を、業種名の昇順でSAMPLE_SECTOR_LIMIT件選ぶ。

    accounting_standardが未設定（＝財務データ未取得）の企業に限定する。既に取得済みの
    企業を選ぶと、FR-11のスキップ判定により0秒・0リクエストという無意味な結果になり、
    キャッシュの効果を測定できないため（サイクル8 FR-46）。
    """
    companies = (
        session.query(Company)
        .filter(Company.accounting_standard.is_(None))
        .order_by(Company.sector, Company.code)
        .all()
    )
    seen_sectors: set[str | None] = set()
    sample: list[Company] = []
    for company in companies:
        if company.sector in seen_sectors:
            continue
        seen_sectors.add(company.sector)
        sample.append(company)
        if len(sample) >= SAMPLE_SECTOR_LIMIT:
            break
    return sample


def find_edinet_code(company_code: str) -> str | None:
    """companies.code（4桁）に対応するedinet_codeをEDINETコードリストから逆引きする"""
    for filer in edinet_client.list_all_filers():
        if filer.sec_code is not None and edinet_client.to_company_code(filer.sec_code) == company_code:
            return filer.edinet_code
    return None


def main() -> None:
    with SessionLocal() as session:
        sample = select_sample_companies(session)

    results = []
    for company in sample:
        edinet_code = find_edinet_code(company.code)
        if edinet_code is None:
            logger.warning("edinet_codeが見つかりません: code=%s", company.code)
            continue

        _states[company.code] = schemas.DownloadStatus(
            status=schemas.DownloadOverallStatus.IN_PROGRESS, logs=[]
        )
        edinet_client.reset_request_count()
        start = time.perf_counter()
        run_download_job(company.code, edinet_code, schemas.DownloadPeriod(type="all"))
        elapsed = time.perf_counter() - start

        state = _states[company.code]
        request_count = edinet_client.get_request_count()
        results.append((company.code, company.name, elapsed, request_count, state.status))
        logger.info(
            "code=%s name=%s 所要時間=%.1f秒 リクエスト数=%d ステータス=%s",
            company.code, company.name, elapsed, request_count, state.status,
        )

    total_seconds = sum(r[2] for r in results)
    total_requests = sum(r[3] for r in results)
    logger.info(
        "=== 集計：%d社、合計%.1f秒、合計%dリクエスト、1社あたり平均%.1f秒/%.1fリクエスト ===",
        len(results), total_seconds, total_requests,
        total_seconds / len(results) if results else 0,
        total_requests / len(results) if results else 0,
    )


if __name__ == "__main__":
    main()
