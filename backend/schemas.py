from datetime import date
from enum import Enum

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
    net_profit: int | None = None
    total_assets: int | None = None
    total_liabilities: int | None = None


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
    ERROR = "error"


class DownloadLogEntry(BaseModel):
    fiscal_year: str
    status: DownloadLogStatus
    message: str


class DownloadStatus(BaseModel):
    """docs/design/api/components/schemas/DownloadStatus.yaml"""

    status: DownloadOverallStatus
    logs: list[DownloadLogEntry]


class ErrorResponse(BaseModel):
    """docs/design/api/components/schemas/Error.yaml

    openapi.yaml上のスキーマ名は"Error"だが、Python標準の例外クラスや
    このプロジェクトの例外クラス群（EdinetApiError等）と紛らわしいため
    ErrorResponseという名前にする。
    """

    error: str
    message: str
