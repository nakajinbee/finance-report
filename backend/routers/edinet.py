import threading
from datetime import date

from fastapi import APIRouter, BackgroundTasks
from fastapi.responses import JSONResponse

import edinet_client
import schemas
import xbrl_parser
from database import Company, Fact, SessionLocal

# SCR-001（ダウンロード画面、docs/design/screen/SCR-001_download.md）向けのAPI-EDN-*系エンドポイント。
#
# TODO(cycle2): docs/design/api/paths/edinet/ 配下（openapi.yaml）はサイクル2向けに改訂済みだが、
# このファイルの実装はまだサイクル1のAPI仕様のまま（このコメントの下に個別箇所を明記）。
# サイクル2実装（FR-06〜FR-11）は次のステップで行う。
router = APIRouter()

# サイクル1はリクルートHD固定（docs/development/backend_implementation_policy.md
# 「実装の思想」原則5：スコープ外の先取りをしない）。
# EDINETの証券コード(secCode)は5桁だがDBのcodeは4桁（実機確認済み、末尾の"0"が異なる）。
#
# TODO(cycle2 FR-07): 企業検索（API-EDN-003 `GET /api/edinet/companies/search`）が未実装のため、
# 引き続きリクルートHD固定。企業検索を実装したらこの定数群とダウンロード対象の決め打ちを撤廃する。
RECRUIT_DB_CODE = "6098"
RECRUIT_EDINET_SEC_CODE = "60980"
RECRUIT_EDINET_CODE = "E07801"
RECRUIT_ACCOUNTING_STANDARD = "IFRS"
# 有価証券報告書の提出日探索の起点（3月決算・6月中旬提出が中心という実機検証結果に基づく）
#
# TODO(cycle2 FR-09、重要): cycle2_requirements.md FR-09で「探索起点日は企業の決算月から
# 動的に算出する」と設計済み（EDINETコードリストの「決算日」列を使う。サイクル2セルフレビューで
# 発覚した重要な抜け漏れ：3月決算でない企業の探索が正しく動かない問題への対応）。
# このファイルはまだ対応しておらず、3月決算固定のまま（＝リクルートHD固定である現状の
# RECRUIT_DB_CODE等と整合しているため当面は問題ないが、企業検索(FR-07)を実装する際は
# 必ずこちらも直すこと）。
ANNUAL_REPORT_SEARCH_MONTH = 6
ANNUAL_REPORT_SEARCH_DAY = 20

# TODO(cycle2 FR-10): 同時ダウンロード制御を企業単位にする設計（`company_code`をキーにした
# 辞書で管理）だが、ここではサイクル1のままアプリ全体で単一の状態を持っている
# （企業検索が未実装で対象企業が常に1社のため、実害はまだない）。
_state = schemas.DownloadStatus(status=schemas.DownloadOverallStatus.IDLE, logs=[])
_state_lock = threading.Lock()


def get_last_five_fiscal_year_ends(today: date) -> list[int]:
    """直近5期分の会計年度（3月期）を、実行日を基準に動的に算出する

    3月決算・6月中旬〜下旬提出が前提のため、7月以降であれば当年の有価証券報告書は
    提出済みとみなせる。6月以前であれば前年までが直近の提出済み分となる。

    TODO(cycle2 FR-09): 本来は決算日から動的算出すべき
    （上のANNUAL_REPORT_SEARCH_MONTH/DAYのコメント参照）。関数名・実装ともサイクル1のまま。
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


def _upsert_facts(
    session, company_code: str, doc_id: str, doc_type_code: str, period_end: date, metrics: xbrl_parser.FinancialMetrics
) -> None:
    """FinancialMetricsの5指標をTBL-003 factsへ保存する

    TODO(cycle2 FR-04/FR-06): xbrl_parser.pyがまだ5指標だけを抽出する設計（サイクル1のまま）のため、
    ここではIFRS用の要素ID・コンテキストIDのマッピングを流用している。
    FR-04（全数値データの取り込み）・FR-06（会計基準3種対応）に沿った本実装は次のステップで行う。
    """
    element_map = xbrl_parser.IfrsXbrlCsvParser._ELEMENT_ID_TO_METRIC
    metric_values = {
        "revenue": metrics.revenue,
        "operating_profit": metrics.operating_profit,
        "net_profit": metrics.net_profit,
        "total_assets": metrics.total_assets,
        "total_liabilities": metrics.total_liabilities,
    }
    for metric_name, value in metric_values.items():
        if value is None:
            continue
        element_id, context_id = element_map[metric_name]
        fact = (
            session.query(Fact)
            .filter_by(company_code=company_code, doc_id=doc_id, element_id=element_id, context_id=context_id)
            .one_or_none()
        )
        if fact is None:
            fact = Fact(company_code=company_code, doc_id=doc_id, element_id=element_id, context_id=context_id)
            session.add(fact)
        fact.doc_type_code = doc_type_code
        fact.period_end = period_end
        fact.value = value


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
                _upsert_facts(session, RECRUIT_DB_CODE, document["docID"], document["docTypeCode"], period_end, metrics)
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
    """API-EDN-001: 財務データのダウンロード開始（SCR-001 データ取得ボタン）

    TODO(cycle2 FR-07/FR-09): docs/design/api/paths/edinet/download.yaml（サイクル2）は
    リクエストボディにcompany_code・edinet_code・period（全期間／年度範囲）を要求する設計だが、
    この実装はまだ無引数のサイクル1仕様のまま（リクルートHD・直近5期固定）。
    """
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
    """API-EDN-002: ダウンロード進捗確認（SCR-001 取得ログエリア）

    TODO(cycle2 FR-10): docs/design/api/paths/edinet/download_status.yaml（サイクル2）は
    company_codeクエリパラメータを必須とする設計（企業単位の進捗管理）だが、
    この実装は無引数のまま単一の`_state`を返している。
    """
    return _state
