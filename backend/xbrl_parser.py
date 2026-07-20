import csv
import io
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation


class XbrlParseError(Exception):
    """CSVのパースに失敗した場合（フォーマット不正・ヘッダ不一致・要素が見つからない等）"""


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

# テキストブロック要素（事業の内容等の長文記載）は単位列が"－"になる（FR-04で対象外とする）
_TEXT_BLOCK_UNIT = "－"

ACCOUNTING_STANDARD_ELEMENT_ID = "jpdei_cor:AccountingStandardsDEI"
ACCOUNTING_STANDARD_CONTEXT_ID = "FilingDateInstant"


@dataclass
class NumericFact:
    """CSV1行分の数値データ（TBL-003 facts の1行に対応）"""

    element_id: str
    element_name: str | None
    context_id: str
    consolidated_or_individual: str | None
    period_or_instant: str | None
    unit: str | None
    value: Decimal


def _read_csv_rows(csv_bytes: bytes) -> csv.DictReader:
    try:
        text = csv_bytes.decode("utf-16")
    except UnicodeDecodeError as e:
        raise XbrlParseError(f"CSVの文字コードがUTF-16として読み取れません: {e}") from e

    reader = csv.DictReader(io.StringIO(text), delimiter="\t")
    if reader.fieldnames is None or list(reader.fieldnames) != EXPECTED_CSV_HEADER:
        raise XbrlParseError(f"CSVのヘッダが想定と異なります: {reader.fieldnames}")
    return reader


def parse_numeric_facts(csv_bytes: bytes) -> list[NumericFact]:
    """提出本文書CSVから数値データの行をすべて抽出する（FR-04）

    会計基準（IFRS/日本基準/米国基準）を問わず、CSVの列構造は共通のため、
    この関数は会計基準を意識しない。会計基準ごとに「どの要素IDが売上高か」といった
    マッピングは backend/metric_mappings.py（API層側の関心事）を参照。
    """
    reader = _read_csv_rows(csv_bytes)

    facts_by_key: dict[tuple[str, str], NumericFact] = {}
    for row in reader:
        if row["単位"] == _TEXT_BLOCK_UNIT:
            continue  # テキストブロック行は除外(FR-04)
        try:
            value = Decimal(row["値"])
        except (InvalidOperation, KeyError):
            continue

        # 同一(要素ID, コンテキストID)が複数行存在することがある（実データ検証済み）ため、
        # 最初の行を採用する
        key = (row["要素ID"], row["コンテキストID"])
        facts_by_key.setdefault(
            key,
            NumericFact(
                element_id=row["要素ID"],
                element_name=row["項目名"] or None,
                context_id=row["コンテキストID"],
                consolidated_or_individual=row["連結・個別"] or None,
                period_or_instant=row["期間・時点"] or None,
                unit=row["単位"] or None,
                value=value,
            ),
        )

    return list(facts_by_key.values())


def extract_accounting_standard(csv_bytes: bytes) -> str:
    """CSVのDEI要素から会計基準を読み取る（FR-06、実機検証済み）

    戻り値は "IFRS" / "Japan GAAP" / "US GAAP" のいずれか（EDINETのDEI要素の値そのまま）。
    この要素は単位が"－"のテキスト値のため parse_numeric_facts の対象外であり、
    別関数として読む必要がある。
    """
    reader = _read_csv_rows(csv_bytes)
    for row in reader:
        if row["要素ID"] == ACCOUNTING_STANDARD_ELEMENT_ID and row["コンテキストID"] == ACCOUNTING_STANDARD_CONTEXT_ID:
            return row["値"]

    raise XbrlParseError(f"{ACCOUNTING_STANDARD_ELEMENT_ID} が見つかりません")
