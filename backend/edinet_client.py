import calendar
import csv
import io
import os
import re
import time
import zipfile
from dataclasses import dataclass
from datetime import date, timedelta

import requests
from dotenv import load_dotenv

load_dotenv()

EDINET_API_KEY = os.environ["EDINET_API_KEY"]
BASE_URL = "https://api.edinet-fsa.go.jp/api/v2"
# EDINETコードリスト（提出者マスタ）のダウンロードURL。api.edinet-fsa.go.jp とは別ホストの
# 静的ファイル配信であり、Subscription-Key不要・レート制限の対象外（実機確認済み）。
FILER_INFO_URL = "https://disclosure2dl.edinet-fsa.go.jp/searchdocument/codelist/Edinetcode.zip"
FILER_INFO_CSV_NAME = "EdinetcodeDlInfo.csv"
REQUEST_TIMEOUT_SECONDS = 15
# EDINET APIの429(Too Many Requests)を避けるための最小リクエスト間隔
# memo/リクルートデータ取得メモ.md の実機検証で採用した間隔と同じ
MIN_REQUEST_INTERVAL_SECONDS = 0.6
# 通信の一時的な瞬断（ConnectTimeout等）に対するリトライ回数・待機秒数
# （サイクル9のバックフィル実行中に実際にタイムアウトが発生し追加。長時間のバッチ処理が
# 通信の瞬断1回で全体停止しないようにする）
TRANSIENT_ERROR_MAX_RETRIES = 3
TRANSIENT_ERROR_RETRY_WAIT_SECONDS = 5

# 書類種別コード：有価証券報告書（訂正版の"130"は含まない）
DOC_TYPE_CODE_ANNUAL_REPORT = "120"
# 書類種別コード：半期報告書（訂正版の"170"は含まない、FR-08）
DOC_TYPE_CODE_SEMI_ANNUAL_REPORT = "160"
# 書類取得APIの必要書類コード：CSV（XBRLをCSVに変換したもの）
DOCUMENT_TYPE_CSV = 5
# 書類取得APIのZIPから取り出す提出本文書CSVのファイル名プレフィックス（書類種別ごと）。
# 半期報告書は制度移行期のため複数のプレフィックスが存在する（実機確認済み）：
# "ssr"＝2025年9月期以降の半期報告書、"q2r"＝2024年9月期（旧・四半期報告書からの移行期）。
REPORT_CSV_PREFIXES = {
    DOC_TYPE_CODE_ANNUAL_REPORT: ["jpcrp030000-asr-001_"],
    DOC_TYPE_CODE_SEMI_ANNUAL_REPORT: ["jpcrp040300-ssr-001_", "jpcrp040300-q2r-001_"],
}
# 提出期限の目安（決算期間終了日からの日数）。有価証券報告書は3ヶ月以内、
# 半期報告書は45日以内（FR-08、docs/requirements/cycle2_requirements.md 実機検証済み）
REPORT_FILING_DEADLINE_DAYS = {
    DOC_TYPE_CODE_ANNUAL_REPORT: 90,
    DOC_TYPE_CODE_SEMI_ANNUAL_REPORT: 45,
}

_last_request_time: float = 0.0
_request_count: int = 0
_document_list_cache: dict[date, list[dict]] = {}


class EdinetApiError(Exception):
    """EDINET APIがエラーを返した場合の基底例外"""


class EdinetRateLimitError(EdinetApiError):
    """429 Too Many Requests"""


class EdinetDocumentNotFoundError(EdinetApiError):
    """対象の書類が見つからない場合（該当書類0件、またはEDINET側が書類取得エラーを返した場合）"""


class EdinetAuthError(EdinetApiError):
    """APIキーが無効な場合（401）"""


def _wait_for_rate_limit() -> None:
    global _last_request_time
    elapsed = time.monotonic() - _last_request_time
    if elapsed < MIN_REQUEST_INTERVAL_SECONDS:
        time.sleep(MIN_REQUEST_INTERVAL_SECONDS - elapsed)


def get_request_count() -> int:
    """直近のreset_request_count()以降に行われたEDINETへのHTTPリクエスト回数を返す
    （サイクル7 FR-42、バッチ取得の技術検証用）"""
    return _request_count


def reset_request_count() -> None:
    """リクエストカウンタを0に戻す（企業ごとに区切って計測するため）"""
    global _request_count
    _request_count = 0


def _get(path: str, params: dict) -> requests.Response:
    """HTTPレベルの通信のみを行う。EDINET APIはエラー時もHTTP 200を返す仕様のため、
    ステータスコードでの成否判定はここでは行わない（429のみ例外）。
    書類一覧API・書類取得APIそれぞれのエラー判定は呼び出し元で行う
    （memo/リクルートデータ取得メモ.md および EDINET_API_仕様書.pdf 3-3節「書類取得APIを
    利用する際のリクエスト結果の判定について」参照）。
    """
    _wait_for_rate_limit()
    global _last_request_time
    global _request_count
    _request_count += 1

    for attempt in range(1, TRANSIENT_ERROR_MAX_RETRIES + 1):
        try:
            response = requests.get(
                f"{BASE_URL}{path}",
                params={**params, "Subscription-Key": EDINET_API_KEY},
                timeout=REQUEST_TIMEOUT_SECONDS,
            )
            break
        except (requests.exceptions.ConnectionError, requests.exceptions.Timeout):
            if attempt == TRANSIENT_ERROR_MAX_RETRIES:
                raise
            time.sleep(TRANSIENT_ERROR_RETRY_WAIT_SECONDS)
    _last_request_time = time.monotonic()

    if response.status_code == 429:
        raise EdinetRateLimitError(f"EDINET APIのレート制限に達しました: {path}")

    # 401（APIキー無効）はHTTPステータス200のまま、他のエラー（400/404/500）とは異なる
    # JSON形状（{"StatusCode": 401, "message": ...}、metadataでラップされない）で返る
    # （EDINET_API_仕様書.pdf 3-3節、2026-07-22実機確認。FR-21調査の過程で発見）。
    # 書類取得APIはZIPバイナリを返す場合がありJSONとして読めないため、失敗時のみ判定する
    try:
        body = response.json()
    except ValueError:
        body = None
    if isinstance(body, dict) and body.get("StatusCode") == 401:
        raise EdinetAuthError(f"EDINET APIキーが無効です: {body.get('message')}")

    return response


def fetch_document_list(target_date: date) -> list[dict]:
    """書類一覧API(type=2)を呼び、指定日の提出書類一覧(results)を返す

    書類一覧APIは成功・失敗どちらもHTTP 200で返るため、レスポンスJSON内の
    metadata.status で成否を判定する。

    同一日付への2回目以降の呼び出しはプロセス内キャッシュから返す（サイクル8
    FR-45）。異なる企業のsearch_reportが同じ日付範囲を探索することが多く
    （決算期が集中する3月末近辺等）、EDINETへの重複リクエストが多いことが
    サイクル7の実測で判明したため。過去日の提出履歴は後から変わらないため、
    キャッシュに陳腐化のリスクはない（本関数は未来日を渡されない前提。
    search_report側で既に未来日を除外している）。
    """
    if target_date in _document_list_cache:
        return _document_list_cache[target_date]

    response = _get(
        "/documents.json",
        {"date": target_date.isoformat(), "type": 2},
    )
    body = response.json()
    status = body.get("metadata", {}).get("status")
    if status != "200":
        message = body.get("metadata", {}).get("message", "unknown error")
        raise EdinetApiError(f"書類一覧APIがエラーを返しました: status={status}, message={message}")
    results = body.get("results") or []
    _document_list_cache[target_date] = results
    return results


def find_report(documents: list[dict], sec_code: str, doc_type_code: str) -> dict | None:
    """documents から指定docTypeCode かつ secCode一致の書類を1件返す（見つからなければNone）"""
    for document in documents:
        if document.get("secCode") == sec_code and document.get("docTypeCode") == doc_type_code:
            return document
    return None


def search_report(sec_code: str, around_date: date, doc_type_code: str, window_days: int = 25) -> dict:
    """around_dateを起点に前後window_days日の範囲で指定書類種別を探索して返す。

    提出日は年によって数日〜1週間前後ずれるため、日付を1日ずつ広げながら探索する
    （memo/リクルートデータ取得メモ.md Step2の検証スクリプトと同じロジック）。
    見つからなければEdinetDocumentNotFoundErrorを送出する。

    未来日（本日より後の日付）は候補から除外する。EDINETは未来日のデータを持たず
    metadata.status="404"（リソースが存在しない）を返すため、fetch_document_listが
    例外を送出し、まだ確認していない過去日側の候補が残っていても探索全体が中断して
    しまうことを避ける（FR-21、2026-07-22実機確認：オムニ・プラス・システム・リミテッド
    E36713の探索で発生）。
    """
    today = date.today()
    for offset in range(0, window_days + 1):
        for sign in ([0] if offset == 0 else [1, -1]):
            candidate_date = around_date + timedelta(days=offset * sign)
            if candidate_date > today:
                continue
            documents = fetch_document_list(candidate_date)
            report = find_report(documents, sec_code, doc_type_code)
            if report is not None:
                return report

    raise EdinetDocumentNotFoundError(
        f"sec_code={sec_code}, docTypeCode={doc_type_code} の書類が "
        f"{around_date} の前後{window_days}日以内に見つかりませんでした"
    )


def fetch_report_csv(doc_id: str, doc_type_code: str) -> bytes:
    """書類取得API(type=5)でCSVのZIPを取得し、ZIP内の提出本文書CSVの生バイト列を返す

    書類取得APIは成功時（ZIP）と失敗時（JSON）でContent-Typeが異なるだけで
    HTTPステータスはどちらも200になりうるため、Content-Typeで成否を判定する。
    デコード・パースはxbrl_parser.pyの責務なのでここでは行わない。
    """
    response = _get(
        f"/documents/{doc_id}",
        {"type": DOCUMENT_TYPE_CSV},
    )
    content_type = response.headers.get("Content-Type", "")
    if "application/octet-stream" not in content_type:
        metadata = response.json().get("metadata", {})
        raise EdinetDocumentNotFoundError(
            f"doc_id={doc_id} の書類取得に失敗しました: "
            f"status={metadata.get('status')}, message={metadata.get('message')}"
        )

    csv_prefixes = REPORT_CSV_PREFIXES[doc_type_code]
    with zipfile.ZipFile(io.BytesIO(response.content)) as archive:
        for name in archive.namelist():
            basename = name.split("/")[-1]
            if any(basename.startswith(prefix) for prefix in csv_prefixes):
                return archive.read(name)

    raise EdinetApiError(f"doc_id={doc_id} のZIPに提出本文書CSVが含まれていません")


@dataclass
class FilerInfo:
    """EDINETコードリストから取得した提出者情報"""

    edinet_code: str
    name: str
    sector: str | None
    sec_code: str | None
    fiscal_year_end_month: int | None
    fiscal_year_end_day: int | None


_FISCAL_YEAR_END_PATTERN = re.compile(r"(\d+)月(\d+)日")
# 「N月末日」表記（例："8月末日"）向け。日付を明記せず月末を指す企業が存在する
# （良品計画E03248で実機確認、FR-19）。何日が月末かは年（うるう年等）によって変わるため、
# ここではFISCAL_YEAR_END_LAST_DAY_OF_MONTHという特別な値を返し、実際の日付が必要になった
# 時点（年が確定した時点）でfiscal_year_end_date()を使って解決する
_FISCAL_YEAR_END_MONTH_END_PATTERN = re.compile(r"(\d+)月末日")
FISCAL_YEAR_END_LAST_DAY_OF_MONTH = 0

_filer_info_cache: list[FilerInfo] | None = None


def _parse_fiscal_year_end(raw: str) -> tuple[int | None, int | None]:
    """EDINETコードリストの「決算日」列（例："3月31日"・"8月末日"）をパースする

    ファンド等、決算日が空文字列の行もあるため、パースできない場合は(None, None)。
    全11,353件（2026-07-22時点）を実機スキャンし、空文字列以外に未対応の表記が
    ないことを確認済み（docs/requirements/cycle3_requirements.md FR-19参照）。
    """
    month_end_match = _FISCAL_YEAR_END_MONTH_END_PATTERN.match(raw)
    if month_end_match is not None:
        return int(month_end_match.group(1)), FISCAL_YEAR_END_LAST_DAY_OF_MONTH

    match = _FISCAL_YEAR_END_PATTERN.match(raw)
    if match is None:
        return None, None
    return int(match.group(1)), int(match.group(2))


def _resolve_fiscal_year_end_day(year: int, month: int, day: int) -> int:
    """fiscal_year_end_dayがFISCAL_YEAR_END_LAST_DAY_OF_MONTHの場合、実際の月末日に解決する"""
    if day == FISCAL_YEAR_END_LAST_DAY_OF_MONTH:
        return calendar.monthrange(year, month)[1]
    return day


def fiscal_year_end_date(fiscal_year_end_month: int, fiscal_year_end_day: int, year: int) -> date:
    """決算月日とyearから実際のdateを構築する（「N月末日」表記の解決を含む、FR-19）"""
    day = _resolve_fiscal_year_end_day(year, fiscal_year_end_month, fiscal_year_end_day)
    return date(year, fiscal_year_end_month, day)


def _load_filer_info_cache() -> list[FilerInfo]:
    """EDINETコードリスト(EdinetcodeDlInfo.csv)をダウンロード・パースし、プロセス起動中
    メモリキャッシュする（NFR-05：検索のたびに再取得しない。プロセス再起動まで再取得しない）。

    このCSVはCP932(Shift-JIS)エンコードで、1行目はダウンロード実行日等のサマリ行、
    2行目がヘッダ行（実機確認済み）。
    """
    global _filer_info_cache
    if _filer_info_cache is not None:
        return _filer_info_cache

    response = requests.get(FILER_INFO_URL, timeout=REQUEST_TIMEOUT_SECONDS)
    if response.status_code != 200:
        raise EdinetApiError(f"EDINETコードリストの取得に失敗しました: status={response.status_code}")

    with zipfile.ZipFile(io.BytesIO(response.content)) as archive:
        raw_bytes = archive.read(FILER_INFO_CSV_NAME)

    text = raw_bytes.decode("cp932")
    data_lines = text.splitlines()[1:]  # 1行目のサマリ行をスキップ
    reader = csv.DictReader(data_lines)

    filers = []
    for row in reader:
        fiscal_year_end_month, fiscal_year_end_day = _parse_fiscal_year_end(row["決算日"])
        filers.append(
            FilerInfo(
                edinet_code=row["ＥＤＩＮＥＴコード"],
                name=row["提出者名"],
                sector=row["提出者業種"] or None,
                sec_code=row["証券コード"] or None,
                fiscal_year_end_month=fiscal_year_end_month,
                fiscal_year_end_day=fiscal_year_end_day,
            )
        )

    _filer_info_cache = filers
    return _filer_info_cache


def list_all_filers() -> list[FilerInfo]:
    """EDINETコードリストの全提出者を返す（サイクル6 FR-39、一括登録バッチ用）"""
    return _load_filer_info_cache()


def to_company_code(sec_code: str) -> str:
    """EDINETの証券コード（5桁、末尾0）を、companiesテーブルの4桁codeに変換する
    （サイクル6 FR-39で追加、サイクル7 FR-43でも共用するためここに集約）。
    """
    if not sec_code.endswith("0"):
        raise ValueError(f"末尾が0でない証券コード: {sec_code}")
    return sec_code[:-1]


def fetch_filer_info(edinet_code: str) -> FilerInfo:
    """EDINETコードリストから指定edinet_codeの提出者情報を1件返す"""
    for filer in _load_filer_info_cache():
        if filer.edinet_code == edinet_code:
            return filer

    raise EdinetDocumentNotFoundError(f"EDINETコードリストに edinet_code={edinet_code} が見つかりません")


def search_filers(query: str, limit: int = 20) -> list[FilerInfo]:
    """EDINETコードリストから企業名・証券コードの部分一致で検索する（FR-07）"""
    query = query.strip()
    if not query:
        return []

    matches = [
        filer
        for filer in _load_filer_info_cache()
        if query in filer.name or (filer.sec_code is not None and query in filer.sec_code)
    ]
    return matches[:limit]


def determine_latest_available_fiscal_year(today: date, fiscal_year_end_month: int, fiscal_year_end_day: int) -> int:
    """直近で提出済みとみなせる決算年を、実行日と決算日を基準に動的に算出する（FR-09）

    有価証券報告書は決算日から3ヶ月以内の提出が義務のため、「今年が決算年」の決算日+90日
    （＝提出期限の目安）を過ぎていれば当年分は提出済みとみなせる。過ぎていなければ
    前年分までが直近の提出済み分となる（memo/リクルートデータ取得メモ.md の3月決算固定
    ロジックを任意の決算月日に一般化したもの。dateの加減算で年またぎも自動的に扱える）。
    """
    fiscal_year_end_this_year = fiscal_year_end_date(fiscal_year_end_month, fiscal_year_end_day, today.year)
    filing_deadline = fiscal_year_end_this_year + timedelta(days=90)
    return today.year if today >= filing_deadline else today.year - 1


def _shift_months(base: date, months: int) -> date:
    """baseからmonths ヶ月前の日付を返す（月末日はcalendar.monthrangeでクランプする）

    例：8月31日の6ヶ月前は2月31日が存在しないため2月28日/29日になる。
    """
    month_index = base.month - 1 - months
    year = base.year + month_index // 12
    month = month_index % 12 + 1
    day = min(base.day, calendar.monthrange(year, month)[1])
    return date(year, month, day)


# 半期報告書制度の開始日：2024年4月1日以後に開始する事業年度から、四半期報告書に代わり
# 半期報告書の提出が義務化された。それより前に開始した事業年度には半期報告書は存在しない
# （2026-07-20、リクルートHDの実機検証で確認：2024年4月1日開始の事業年度＝2025年3月期の
# 半期＝2024年9月期分は存在したが、2023年4月1日開始の事業年度＝2024年3月期の半期＝
# 2023年9月期分は存在しなかった）
SEMI_ANNUAL_REPORT_TRANSITION_DATE = date(2024, 4, 1)


def fiscal_year_start(fiscal_year_end_month: int, fiscal_year_end_day: int, target_year: int) -> date:
    """target_year年の決算に対応する事業年度の開始日を返す（前年の決算日の翌日）"""
    previous_fiscal_year_end = fiscal_year_end_date(fiscal_year_end_month, fiscal_year_end_day, target_year - 1)
    return previous_fiscal_year_end + timedelta(days=1)


def semi_annual_report_required(fiscal_year_end_month: int, fiscal_year_end_day: int, target_year: int) -> bool:
    """target_year年の決算に対応する事業年度に、半期報告書の提出義務があるかを返す（FR-08）

    義務化前の年度をEDINETへ探索しても書類が存在せず必ずエラーになるだけのため、
    探索自体を行わないようにする（無駄なEDINETアクセスを避ける、FR-11と同じ考え方）。
    """
    return fiscal_year_start(fiscal_year_end_month, fiscal_year_end_day, target_year) >= SEMI_ANNUAL_REPORT_TRANSITION_DATE


def half_fiscal_year_end(fiscal_year_end_month: int, fiscal_year_end_day: int, target_year: int) -> date:
    """target_year年の決算に対応する半期末日を返す（決算日の6ヶ月前、FR-08）"""
    fiscal_year_end = fiscal_year_end_date(fiscal_year_end_month, fiscal_year_end_day, target_year)
    return _shift_months(fiscal_year_end, 6)


def report_search_center(
    fiscal_year_end_month: int, fiscal_year_end_day: int, target_year: int, doc_type_code: str
) -> date:
    """target_year年の決算に対応する指定書類種別の探索起点日を返す（FR-09・FR-08）

    有価証券報告書は決算日、半期報告書は半期末日を基準に、それぞれの提出期限日数
    （REPORT_FILING_DEADLINE_DAYS）を加えた日を起点とする
    （search_reportのwindow_days=25とあわせて実務上の提出日ゆらぎを吸収する）。
    """
    if doc_type_code == DOC_TYPE_CODE_SEMI_ANNUAL_REPORT:
        period_end = half_fiscal_year_end(fiscal_year_end_month, fiscal_year_end_day, target_year)
    else:
        period_end = fiscal_year_end_date(fiscal_year_end_month, fiscal_year_end_day, target_year)
    return period_end + timedelta(days=REPORT_FILING_DEADLINE_DAYS[doc_type_code])
