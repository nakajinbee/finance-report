import threading
from datetime import date

from fastapi import APIRouter, BackgroundTasks
from fastapi.responses import JSONResponse

import edinet_client
import schemas
import xbrl_parser
from database import Company, Financial, SessionLocal

router = APIRouter()

# サイクル1はリクルートHD固定（docs/development/backend_implementation_policy.md
# 「実装の思想」原則5：スコープ外の先取りをしない）。
# EDINETの証券コード(secCode)は5桁だがDBのcodeは4桁（実機確認済み、末尾の"0"が異なる）。
RECRUIT_DB_CODE = "6098"
RECRUIT_EDINET_SEC_CODE = "60980"
RECRUIT_EDINET_CODE = "E07801"
RECRUIT_ACCOUNTING_STANDARD = "IFRS"
# 有価証券報告書の提出日探索の起点（3月決算・6月中旬提出が中心という実機検証結果に基づく）
ANNUAL_REPORT_SEARCH_MONTH = 6
ANNUAL_REPORT_SEARCH_DAY = 20

_state = schemas.DownloadStatus(status=schemas.DownloadOverallStatus.IDLE, logs=[])
_state_lock = threading.Lock()


def get_last_five_fiscal_year_ends(today: date) -> list[int]:
    """直近5期分の会計年度（3月期）を、実行日を基準に動的に算出する

    3月決算・6月中旬〜下旬提出が前提のため、7月以降であれば当年の有価証券報告書は
    提出済みとみなせる。6月以前であれば前年までが直近の提出済み分となる。
    """
    latest_year = today.year if today.month >= 7 else today.year - 1
    return [latest_year - i for i in range(5)]


def _upsert_company(session, company_code: str, name: str, sector: str | None, accounting_standard: str) -> None:
    company = session.get(Company, company_code)
    if company is None:
        company = Company(code=company_code)
        session.add(company)
    company.name = name
    company.sector = sector
    company.accounting_standard = accounting_standard


def _upsert_financial(session, company_code: str, period_end: date, fiscal_year: str, metrics: xbrl_parser.FinancialMetrics) -> None:
    financial = (
        session.query(Financial)
        .filter_by(company_code=company_code, period_end=period_end)
        .one_or_none()
    )
    if financial is None:
        financial = Financial(company_code=company_code, period_end=period_end)
        session.add(financial)
    financial.fiscal_year = fiscal_year
    financial.revenue = metrics.revenue
    financial.operating_profit = metrics.operating_profit
    financial.net_profit = metrics.net_profit
    financial.total_assets = metrics.total_assets
    financial.total_liabilities = metrics.total_liabilities


def run_download_job() -> None:
    """EDINETから直近5期分の有価証券報告書を取得し、DBに保存する

    1件失敗しても残りの年度は続行し、1件以上成功していればstatus=doneとする
    （docs/design/screen/items/SCR-001_items.md の状態判定ルールと同じ）。
    """
    target_years = get_last_five_fiscal_year_ends(date.today())
    _state.logs = [
        schemas.DownloadLogEntry(
            fiscal_year=f"{year}年3月期", status=schemas.DownloadLogStatus.PENDING, message="待機中"
        )
        for year in target_years
    ]

    session = SessionLocal()
    try:
        filer_info = edinet_client.fetch_filer_info(RECRUIT_EDINET_CODE)
        _upsert_company(session, RECRUIT_DB_CODE, filer_info.name, filer_info.sector, RECRUIT_ACCOUNTING_STANDARD)
        session.commit()

        any_success = False
        for i, year in enumerate(target_years):
            _state.logs[i].status = schemas.DownloadLogStatus.IN_PROGRESS
            _state.logs[i].message = "取得中"
            try:
                document = edinet_client.search_annual_report(
                    RECRUIT_EDINET_SEC_CODE, date(year, ANNUAL_REPORT_SEARCH_MONTH, ANNUAL_REPORT_SEARCH_DAY)
                )
                csv_bytes = edinet_client.fetch_annual_report_csv(document["docID"])
                metrics = xbrl_parser.get_parser(RECRUIT_ACCOUNTING_STANDARD).parse(csv_bytes)

                period_end = date.fromisoformat(document["periodEnd"])
                fiscal_year = f"{period_end.year}年{period_end.month}月期"
                _upsert_financial(session, RECRUIT_DB_CODE, period_end, fiscal_year, metrics)
                session.commit()

                _state.logs[i].status = schemas.DownloadLogStatus.DONE
                _state.logs[i].message = "取得完了"
                any_success = True
            except Exception as e:
                session.rollback()
                _state.logs[i].status = schemas.DownloadLogStatus.ERROR
                _state.logs[i].message = f"取得に失敗しました: {e}"

        _state.status = schemas.DownloadOverallStatus.DONE if any_success else schemas.DownloadOverallStatus.ERROR
    except Exception as e:
        session.rollback()
        _state.status = schemas.DownloadOverallStatus.ERROR
        for log in _state.logs:
            if log.status in (schemas.DownloadLogStatus.PENDING, schemas.DownloadLogStatus.IN_PROGRESS):
                log.status = schemas.DownloadLogStatus.ERROR
                log.message = f"取得に失敗しました: {e}"
    finally:
        session.close()


@router.post("/download", status_code=202)
def start_download(background_tasks: BackgroundTasks):
    """API-EDN-001: 財務データのダウンロード開始"""
    with _state_lock:
        if _state.status == schemas.DownloadOverallStatus.IN_PROGRESS:
            return JSONResponse(
                status_code=409,
                content=schemas.ErrorResponse(
                    error="DOWNLOAD_IN_PROGRESS", message="すでにダウンロードが進行中です"
                ).model_dump(),
            )
        _state.status = schemas.DownloadOverallStatus.IN_PROGRESS
        _state.logs = []

    background_tasks.add_task(run_download_job)
    return {"status": "started", "message": "ダウンロードを開始しました"}


@router.get("/download/status", response_model=schemas.DownloadStatus)
def get_download_status():
    """API-EDN-002: ダウンロード進捗確認"""
    return _state
