import csv
import io
from abc import ABC, abstractmethod
from dataclasses import dataclass


class XbrlParseError(Exception):
    """CSVのパースに失敗した場合（フォーマット不正・ヘッダ不一致等）"""


@dataclass
class FinancialMetrics:
    """CSV1件（＝書類1件＝1期分）から抽出した5指標"""

    revenue: int | None
    operating_profit: int | None
    net_profit: int | None
    total_assets: int | None
    total_liabilities: int | None


EXPECTED_CSV_HEADER = [
    "要素ID",
    "項目名",
    "コンテキストID",
    "相対年度",
    "連結・個別",
    "期間・時点",
    "ユニットID",
    "単位",
    "値",
]

_CONTEXT_ID_CURRENT_DURATION = "CurrentYearDuration"
_CONTEXT_ID_CURRENT_INSTANT = "CurrentYearInstant"


class XbrlCsvParser(ABC):
    """会計基準ごとのCSVパーサーの共通インターフェース"""

    @abstractmethod
    def parse(self, csv_bytes: bytes) -> FinancialMetrics:
        """1期分のCSV（提出本文書CSV）から5指標を抽出して返す"""


class IfrsXbrlCsvParser(XbrlCsvParser):
    """IFRS企業向けの実装（サイクル1のスコープ、リクルートHDで実機検証済み）

    要素ID・コンテキストIDは docs/requirements/cycle1_requirements.md FR-01 参照。
    """

    _ELEMENT_ID_TO_METRIC: dict[str, tuple[str, str]] = {
        "revenue": ("jpcrp_cor:RevenueIFRSSummaryOfBusinessResults", _CONTEXT_ID_CURRENT_DURATION),
        "operating_profit": ("jpigp_cor:OperatingProfitLossIFRS", _CONTEXT_ID_CURRENT_DURATION),
        "net_profit": (
            "jpcrp_cor:ProfitLossAttributableToOwnersOfParentIFRSSummaryOfBusinessResults",
            _CONTEXT_ID_CURRENT_DURATION,
        ),
        "total_assets": ("jpcrp_cor:TotalAssetsIFRSSummaryOfBusinessResults", _CONTEXT_ID_CURRENT_INSTANT),
        "total_liabilities": ("jpigp_cor:LiabilitiesIFRS", _CONTEXT_ID_CURRENT_INSTANT),
    }

    def parse(self, csv_bytes: bytes) -> FinancialMetrics:
        values_by_element_and_context = self._read_values_by_element_and_context(csv_bytes)

        metric_values: dict[str, int | None] = {}
        for metric_name, (element_id, context_id) in self._ELEMENT_ID_TO_METRIC.items():
            raw_value = values_by_element_and_context.get((element_id, context_id))
            metric_values[metric_name] = int(raw_value) if raw_value not in (None, "") else None

        return FinancialMetrics(**metric_values)

    def _read_values_by_element_and_context(self, csv_bytes: bytes) -> dict[tuple[str, str], str]:
        try:
            text = csv_bytes.decode("utf-16")
        except UnicodeDecodeError as e:
            raise XbrlParseError(f"CSVの文字コードがUTF-16として読み取れません: {e}") from e

        reader = csv.DictReader(io.StringIO(text), delimiter="\t")
        if reader.fieldnames is None or list(reader.fieldnames) != EXPECTED_CSV_HEADER:
            raise XbrlParseError(f"CSVのヘッダが想定と異なります: {reader.fieldnames}")

        values_by_element_and_context: dict[tuple[str, str], str] = {}
        for row in reader:
            key = (row["要素ID"], row["コンテキストID"])
            # 同一キーが複数行存在する場合があるため、最初に見つかった値を採用する
            values_by_element_and_context.setdefault(key, row["値"])

        return values_by_element_and_context


def get_parser(accounting_standard: str) -> XbrlCsvParser:
    """TBL-001.accounting_standard の値からパーサーを選ぶファクトリ関数

    未対応の会計基準はサイレントに間違った値を返さないよう、即座にエラーとする。
    """
    if accounting_standard == "IFRS":
        return IfrsXbrlCsvParser()
    raise NotImplementedError(f"未対応の会計基準です: {accounting_standard}")
