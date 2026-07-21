from datetime import date
from enum import Enum
from typing import Literal

from pydantic import BaseModel


class Company(BaseModel):
    """docs/design/api/components/schemas/Company.yaml"""

    code: str
    name: str
    sector: str | None = None
    accounting_standard: str
    periods: list[date]


class FinancialRecord(BaseModel):
    """docs/design/api/components/schemas/FinancialRecord.yaml"""

    fiscal_year: str
    period_end: date
    revenue: int | None = None
    operating_profit: int | None = None
    ordinary_profit: int | None = None
    net_profit: int | None = None
    total_assets: int | None = None
    total_liabilities: int | None = None
    equity: int | None = None


class CompanyFinancials(BaseModel):
    """docs/design/api/components/schemas/CompanyFinancials.yaml"""

    company: Company
    data: list[FinancialRecord]


class DownloadOverallStatus(str, Enum):
    """DownloadStatus.status の取りうる値"""

    IDLE = "idle"
    IN_PROGRESS = "in_progress"
    DONE = "done"
    ERROR = "error"


class DownloadLogStatus(str, Enum):
    """DownloadStatus.logs[].status の取りうる値"""

    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    DONE = "done"
    SKIPPED = "skipped"
    """既存データがあるためEDINETへの再アクセスをスキップした（FR-11）"""
    ERROR = "error"


class DownloadLogEntry(BaseModel):
    fiscal_year: str
    status: DownloadLogStatus
    message: str


class DownloadStatus(BaseModel):
    """docs/design/api/components/schemas/DownloadStatus.yaml"""

    status: DownloadOverallStatus
    logs: list[DownloadLogEntry]


class EdinetCompanySearchResult(BaseModel):
    """docs/design/api/components/schemas/EdinetCompanySearchResult.yaml（FR-07）"""

    edinet_code: str
    name: str
    sec_code: str | None = None
    sector: str | None = None


class DownloadPeriod(BaseModel):
    """POST /api/download リクエストボディの period（FR-09）"""

    type: Literal["all", "range"]
    from_year: int | None = None
    to_year: int | None = None


class DownloadRequest(BaseModel):
    """POST /api/download リクエストボディ（docs/design/api/paths/edinet/download.yaml）"""

    company_code: str
    edinet_code: str
    period: DownloadPeriod


class CashFlowRecord(BaseModel):
    """docs/design/api/components/schemas/CashFlowRecord.yaml（FR-13）"""

    fiscal_year: str
    period_end: date
    operating_cash_flow: int | None = None
    investing_cash_flow: int | None = None
    financing_cash_flow: int | None = None


class RatioRecord(BaseModel):
    """docs/design/api/components/schemas/RatioRecord.yaml（FR-23〜26）"""

    fiscal_year: str
    period_end: date
    roe: float | None = None
    equity_ratio: float | None = None
    eps: float | None = None
    per: float | None = None
    payout_ratio: float | None = None
    roa: float | None = None
    total_asset_turnover: float | None = None
    operating_margin: float | None = None
    net_margin: float | None = None
    current_ratio: float | None = None
    fixed_ratio: float | None = None
    inventory_turnover: float | None = None


class FactRecord(BaseModel):
    """docs/design/api/components/schemas/FactRecord.yaml（FR-16、SCR-004向け）"""

    element_id: str
    element_name: str | None = None
    doc_type_code: str
    period_end: date
    context_id: str
    consolidated_or_individual: str | None = None
    unit: str | None = None
    value: float


class ErrorResponse(BaseModel):
    """docs/design/api/components/schemas/Error.yaml

    openapi.yaml上のスキーマ名は"Error"だが、Python標準の例外クラスや
    このプロジェクトの例外クラス群（EdinetApiError等）と紛らわしいため
    ErrorResponseという名前にする。
    """

    error: str
    message: str
