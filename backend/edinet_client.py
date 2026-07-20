import io
import os
import time
import zipfile
from datetime import date, timedelta

import requests
from dotenv import load_dotenv

load_dotenv()

EDINET_API_KEY = os.environ["EDINET_API_KEY"]
BASE_URL = "https://api.edinet-fsa.go.jp/api/v2"
REQUEST_TIMEOUT_SECONDS = 15
# EDINET APIの429(Too Many Requests)を避けるための最小リクエスト間隔
# memo/リクルートデータ取得メモ.md の実機検証で採用した間隔と同じ
MIN_REQUEST_INTERVAL_SECONDS = 0.6

# 書類種別コード：有価証券報告書（訂正版の"130"は含まない）
DOC_TYPE_CODE_ANNUAL_REPORT = "120"
# 書類取得APIの必要書類コード：CSV（XBRLをCSVに変換したもの）
DOCUMENT_TYPE_CSV = 5
# 書類取得APIのZIPから取り出す提出本文書CSVのファイル名プレフィックス
ANNUAL_REPORT_CSV_PREFIX = "jpcrp030000-asr-001_"

_last_request_time: float = 0.0


class EdinetApiError(Exception):
    """EDINET APIがエラーを返した場合の基底例外"""


class EdinetRateLimitError(EdinetApiError):
    """429 Too Many Requests"""


class EdinetDocumentNotFoundError(EdinetApiError):
    """対象の書類が見つからない場合（該当書類0件、またはEDINET側が書類取得エラーを返した場合）"""


def _wait_for_rate_limit() -> None:
    global _last_request_time
    elapsed = time.monotonic() - _last_request_time
    if elapsed < MIN_REQUEST_INTERVAL_SECONDS:
        time.sleep(MIN_REQUEST_INTERVAL_SECONDS - elapsed)


def _get(path: str, params: dict) -> requests.Response:
    """HTTPレベルの通信のみを行う。EDINET APIはエラー時もHTTP 200を返す仕様のため、
    ステータスコードでの成否判定はここでは行わない（429のみ例外）。
    書類一覧API・書類取得APIそれぞれのエラー判定は呼び出し元で行う
    （memo/リクルートデータ取得メモ.md および EDINET_API_仕様書.pdf 3-3節「書類取得APIを
    利用する際のリクエスト結果の判定について」参照）。
    """
    _wait_for_rate_limit()
    global _last_request_time
    response = requests.get(
        f"{BASE_URL}{path}",
        params={**params, "Subscription-Key": EDINET_API_KEY},
        timeout=REQUEST_TIMEOUT_SECONDS,
    )
    _last_request_time = time.monotonic()

    if response.status_code == 429:
        raise EdinetRateLimitError(f"EDINET APIのレート制限に達しました: {path}")
    return response


def fetch_document_list(target_date: date) -> list[dict]:
    """書類一覧API(type=2)を呼び、指定日の提出書類一覧(results)を返す

    書類一覧APIは成功・失敗どちらもHTTP 200で返るため、レスポンスJSON内の
    metadata.status で成否を判定する。
    """
    response = _get(
        "/documents.json",
        {"date": target_date.isoformat(), "type": 2},
    )
    body = response.json()
    status = body.get("metadata", {}).get("status")
    if status != "200":
        message = body.get("metadata", {}).get("message", "unknown error")
        raise EdinetApiError(f"書類一覧APIがエラーを返しました: status={status}, message={message}")
    return body.get("results") or []


def find_annual_report(documents: list[dict], sec_code: str) -> dict | None:
    """documents から docTypeCode=='120' かつ secCode一致の書類を1件返す（見つからなければNone）"""
    for document in documents:
        if document.get("secCode") == sec_code and document.get("docTypeCode") == DOC_TYPE_CODE_ANNUAL_REPORT:
            return document
    return None


def search_annual_report(sec_code: str, around_date: date, window_days: int = 25) -> dict:
    """around_dateを起点に前後window_days日の範囲で有価証券報告書を探索して返す。

    提出日は年によって数日〜1週間前後ずれるため、日付を1日ずつ広げながら探索する
    （memo/リクルートデータ取得メモ.md Step2の検証スクリプトと同じロジック）。
    見つからなければEdinetDocumentNotFoundErrorを送出する。
    """
    for offset in range(0, window_days + 1):
        for sign in ([0] if offset == 0 else [1, -1]):
            candidate_date = around_date + timedelta(days=offset * sign)
            documents = fetch_document_list(candidate_date)
            annual_report = find_annual_report(documents, sec_code)
            if annual_report is not None:
                return annual_report

    raise EdinetDocumentNotFoundError(
        f"sec_code={sec_code} の有価証券報告書が {around_date} の前後{window_days}日以内に見つかりませんでした"
    )


def fetch_annual_report_csv(doc_id: str) -> bytes:
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

    with zipfile.ZipFile(io.BytesIO(response.content)) as archive:
        for name in archive.namelist():
            if name.split("/")[-1].startswith(ANNUAL_REPORT_CSV_PREFIX):
                return archive.read(name)

    raise EdinetApiError(f"doc_id={doc_id} のZIPに提出本文書CSVが含まれていません")
