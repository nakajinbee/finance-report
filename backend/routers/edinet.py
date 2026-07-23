import threading
from datetime import date, datetime

from fastapi import APIRouter, BackgroundTasks
from fastapi.responses import JSONResponse

import edinet_client
import schemas
import xbrl_parser
from database import Company, CompanyQuantitativeFact, SessionLocal
from document_list_ingestion import upsert_document_from_row
from quantitative_fact_ingestion import upsert_company, upsert_qualitative_facts, upsert_quantitative_facts

# SCR-001（ダウンロード画面、docs/design/screen/SCR-001_download.md）向けのAPI-EDN-*系エンドポイント。
router = APIRouter()

# 書類探索窓（前後日数）。デフォルトのedinet_client.search_reportと同じ値。
REPORT_SEARCH_WINDOW_DAYS = 25
# 過去に遡る最大年数（EDINET側の閲覧期間上限＝縦覧5年+延長5年、FR-09参照）
MAX_LOOKBACK_YEARS = 10
# 1決算年あたりダウンロード対象とする書類種別（有価証券報告書・半期報告書、FR-08。
# 四半期報告書は実機検証の結果対象4社いずれにも見つからず対象外とした
# ＝docs/requirements/cycle2_requirements.md FR-08参照）
REPORT_TYPES = [
    edinet_client.DOC_TYPE_CODE_ANNUAL_REPORT,
    edinet_client.DOC_TYPE_CODE_SEMI_ANNUAL_REPORT,
]

# 企業ごとの進捗状態（FR-10：同時ダウンロード制御を企業単位にする）。
# _meta_lockはこの辞書の読み書き（多重起動チェック＆初期化）のみを保護する軽量ロック。
# 一度_statesにIN_PROGRESSとして登録された後の実処理はロック外で行うため、
# 異なるcompany_codeは並行して処理できる（同一company_codeは_states[company_code].status
# のチェックにより多重実行がブロックされる）。
_states: dict[str, schemas.DownloadStatus] = {}
_meta_lock = threading.Lock()


def _determine_target_fiscal_years(period: schemas.DownloadPeriod, latest_available_year: int) -> list[int]:
    """period指定（全期間／年度範囲）から対象の決算年一覧を返す（新しい年から順）"""
    if period.type == "all":
        return [latest_available_year - i for i in range(MAX_LOOKBACK_YEARS)]
    return list(range(period.to_year, period.from_year - 1, -1))


def _quantitative_fact_exists_for_period(session, company_code: str, period_end: date) -> bool:
    return (
        session.query(CompanyQuantitativeFact.id)
        .filter_by(company_code=company_code, period_end=period_end)
        .first()
        is not None
    )


def _expected_period_end(filer_info: edinet_client.FilerInfo, year: int, doc_type_code: str) -> date:
    if doc_type_code == edinet_client.DOC_TYPE_CODE_SEMI_ANNUAL_REPORT:
        return edinet_client.half_fiscal_year_end(filer_info.fiscal_year_end_month, filer_info.fiscal_year_end_day, year)
    return edinet_client.fiscal_year_end_date(filer_info.fiscal_year_end_month, filer_info.fiscal_year_end_day, year)


def _fiscal_year_label(period_end: date, doc_type_code: str) -> str:
    label = f"{period_end.year}年{period_end.month}月期"
    if doc_type_code == edinet_client.DOC_TYPE_CODE_SEMI_ANNUAL_REPORT:
        label += "（半期）"
    return label


def run_download_job(company_code: str, edinet_code: str, period: schemas.DownloadPeriod) -> None:
    """指定企業の有価証券報告書・半期報告書をEDINETから取得し、DBに保存する（FR-07/FR-08/FR-09）

    同一企業・同一期間のデータが既にDBに存在する場合はEDINETへ再アクセスせずスキップする
    （FR-11：EDINETへの不要なアクセスを減らす。訂正報告書の反映は自動検知しない設計であり、
    反映が必要な場合はDBの該当データを手動削除してから再ダウンロードする運用とする）。
    1件失敗しても残りの年度・書類種別は続行し、1件以上成功（スキップも成功扱い）していれば
    status=doneとする（docs/design/screen/items/SCR-001_items.md の状態判定ルールと同じ）。
    """
    state = _states[company_code]

    session = SessionLocal()
    try:
        filer_info = edinet_client.fetch_filer_info(edinet_code)
        if filer_info.sec_code is None or filer_info.fiscal_year_end_month is None or filer_info.fiscal_year_end_day is None:
            state.status = schemas.DownloadOverallStatus.ERROR
            state.logs = [
                schemas.DownloadLogEntry(
                    fiscal_year="-",
                    status=schemas.DownloadLogStatus.ERROR,
                    message="この提出者は証券コードまたは決算日が不明なため、ダウンロードできません",
                )
            ]
            return

        latest_available_year = edinet_client.determine_latest_available_fiscal_year(
            date.today(), filer_info.fiscal_year_end_month, filer_info.fiscal_year_end_day
        )
        target_years = _determine_target_fiscal_years(period, latest_available_year)

        # 対象年 x 書類種別（有価証券報告書・半期報告書）の組み合わせを対象にする（FR-08）。
        # 半期報告書は制度上の提出義務化前の年度には存在しないため、その年度は探索自体を
        # 行わない（無駄なEDINETアクセス・確実に失敗するログ行を避ける）
        targets = [
            (year, doc_type_code)
            for year in target_years
            for doc_type_code in REPORT_TYPES
            if doc_type_code != edinet_client.DOC_TYPE_CODE_SEMI_ANNUAL_REPORT
            or edinet_client.semi_annual_report_required(
                filer_info.fiscal_year_end_month, filer_info.fiscal_year_end_day, year
            )
        ]

        state.logs = [
            schemas.DownloadLogEntry(
                fiscal_year=_fiscal_year_label(_expected_period_end(filer_info, year, doc_type_code), doc_type_code),
                status=schemas.DownloadLogStatus.PENDING,
                message="待機中",
            )
            for year, doc_type_code in targets
        ]

        # 会計基準は原則EDINETのDEI要素から確定させるが、既に企業が保存済みならDBの値を使い、
        # 無駄なEDINET通信を避ける（企業が既存でない場合のみ、最初に成功した書類から判定する）
        existing_company = session.get(Company, company_code)
        accounting_standard = existing_company.accounting_standard if existing_company is not None else None

        any_success = False
        for i, (year, doc_type_code) in enumerate(targets):
            expected_period_end = _expected_period_end(filer_info, year, doc_type_code)

            if _quantitative_fact_exists_for_period(session, company_code, expected_period_end):
                state.logs[i].status = schemas.DownloadLogStatus.SKIPPED
                state.logs[i].message = "スキップ（既存データあり）"
                any_success = True
                continue

            state.logs[i].status = schemas.DownloadLogStatus.IN_PROGRESS
            state.logs[i].message = "取得中"
            try:
                center_date = edinet_client.report_search_center(
                    filer_info.fiscal_year_end_month, filer_info.fiscal_year_end_day, year, doc_type_code
                )
                document = edinet_client.search_report(
                    filer_info.sec_code, center_date, doc_type_code, window_days=REPORT_SEARCH_WINDOW_DAYS
                )
                csv_bytes = edinet_client.fetch_report_csv(document["docID"], doc_type_code)

                if accounting_standard is None:
                    accounting_standard = xbrl_parser.extract_accounting_standard(csv_bytes)
                    upsert_company(session, company_code, filer_info.name, filer_info.sector, accounting_standard)
                    session.commit()

                quantitative_facts = xbrl_parser.parse_quantitative_facts(csv_bytes)

                # 書類取得APIのdocument["periodEnd"]は使わず、決算日から算出した期間終了日を
                # 保存する。半期報告書ではEDINET側のperiodEndが対象期間（半期末）ではなく
                # 対象事業年度の期末（年度末）を返すことが実機検証で判明したため
                # （2026-07-20、リクルートHD 2024年9月期半期報告書で確認）。
                upsert_quantitative_facts(
                    session, company_code, document["docID"], document["docTypeCode"], expected_period_end, quantitative_facts
                )

                # documentsテーブルのレコードを作成/更新し、body_ingested_atを設定する
                # （サイクル13 FR-59。個別ダウンロードは長らくdocumentsを更新しておらず、
                # body_ingested_atが「本体取り込み済みか」の実態を反映していなかった）。
                # list_dateはsubmitDateTimeの日付部分で代用する（この書類を発見したのは
                # 書類一覧APIの日次取り込みではなく個別検索のため、正確な取得日は無いが、
                # 進捗管理用の参考値としては提出日で十分）
                list_date = date.fromisoformat(document["submitDateTime"][:10])
                document_row = upsert_document_from_row(session, company_code, list_date, document)

                qualitative_facts = xbrl_parser.parse_qualitative_facts(csv_bytes)
                upsert_qualitative_facts(session, company_code, document["docID"], expected_period_end, qualitative_facts)

                document_row.body_ingested_at = datetime.now()
                session.commit()

                state.logs[i].status = schemas.DownloadLogStatus.DONE
                state.logs[i].message = "取得完了"
                any_success = True
            except Exception as e:
                session.rollback()
                state.logs[i].status = schemas.DownloadLogStatus.ERROR
                state.logs[i].message = f"取得に失敗しました: {e}"

        state.status = schemas.DownloadOverallStatus.DONE if any_success else schemas.DownloadOverallStatus.ERROR
    except Exception as e:
        session.rollback()
        state.status = schemas.DownloadOverallStatus.ERROR
        for log in state.logs:
            if log.status in (schemas.DownloadLogStatus.PENDING, schemas.DownloadLogStatus.IN_PROGRESS):
                log.status = schemas.DownloadLogStatus.ERROR
                log.message = f"取得に失敗しました: {e}"
    finally:
        session.close()


@router.post("/download", status_code=202)
def start_download(request: schemas.DownloadRequest, background_tasks: BackgroundTasks):
    """API-EDN-001: 財務データのダウンロード開始（SCR-001 データ取得ボタン）"""
    if request.period.type == "range":
        if request.period.from_year is None or request.period.to_year is None:
            return JSONResponse(
                status_code=400,
                content=schemas.ErrorResponse(
                    error="INVALID_PERIOD", message="期間指定にはfrom_year・to_yearの両方が必要です"
                ).model_dump(),
            )
        if request.period.from_year > request.period.to_year:
            return JSONResponse(
                status_code=400,
                content=schemas.ErrorResponse(
                    error="INVALID_PERIOD", message="from_yearはto_year以前である必要があります"
                ).model_dump(),
            )

    with _meta_lock:
        current = _states.get(request.company_code)
        if current is not None and current.status == schemas.DownloadOverallStatus.IN_PROGRESS:
            return JSONResponse(
                status_code=409,
                content=schemas.ErrorResponse(
                    error="DOWNLOAD_IN_PROGRESS", message="すでにダウンロードが進行中です"
                ).model_dump(),
            )
        _states[request.company_code] = schemas.DownloadStatus(status=schemas.DownloadOverallStatus.IN_PROGRESS, logs=[])

    background_tasks.add_task(run_download_job, request.company_code, request.edinet_code, request.period)
    return {"status": "started", "message": "ダウンロードを開始しました"}


@router.get("/download/status", response_model=schemas.DownloadStatus)
def get_download_status(company_code: str):
    """API-EDN-002: ダウンロード進捗確認（SCR-001 取得ログエリア）"""
    state = _states.get(company_code)
    if state is None:
        return JSONResponse(
            status_code=404,
            content=schemas.ErrorResponse(
                error="DOWNLOAD_NOT_FOUND", message="指定company_codeのダウンロード履歴が存在しません"
            ).model_dump(),
        )
    return state


@router.get("/edinet/companies/search", response_model=list[schemas.EdinetCompanySearchResult])
def search_edinet_companies(q: str):
    """API-EDN-003: EDINET企業検索（SCR-001 企業検索ボックス、FR-07）"""
    filers = edinet_client.search_filers(q)
    return [
        schemas.EdinetCompanySearchResult(
            edinet_code=filer.edinet_code, name=filer.name, sec_code=filer.sec_code, sector=filer.sector
        )
        for filer in filers
    ]
