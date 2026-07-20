// docs/design/api/openapi.yaml のスキーマ名と1対1になる型定義。
// APIのベースURLは開発用の固定値（秘密情報ではないため .env 化はしない）。
const API_BASE_URL = "http://localhost:8000";

export type Company = {
  code: string;
  name: string;
  sector: string | null;
  accounting_standard: string;
  periods: string[]; // ISO date文字列（YYYY-MM-DD、docs/development/date_format_policy.md準拠）
};

export type FinancialRecord = {
  fiscal_year: string;
  period_end: string;
  revenue: number | null;
  operating_profit: number | null;
  net_profit: number | null;
  total_assets: number | null;
  total_liabilities: number | null;
};

export type CompanyFinancials = {
  company: Company;
  data: FinancialRecord[];
};

export type DownloadLogStatus = "pending" | "in_progress" | "done" | "error";

export type DownloadLogEntry = {
  fiscal_year: string;
  status: DownloadLogStatus;
  message: string;
};

export type DownloadOverallStatus = "idle" | "in_progress" | "done" | "error";

export type DownloadStatus = {
  status: DownloadOverallStatus;
  logs: DownloadLogEntry[];
};

export type ErrorResponse = {
  error: string;
  message: string;
};

export type ApiResult<T> = { ok: true; data: T } | { ok: false; error: ErrorResponse };

async function requestJson<T>(path: string, init?: RequestInit): Promise<ApiResult<T>> {
  const response = await fetch(`${API_BASE_URL}${path}`, init);
  const body = await response.json();
  if (!response.ok) {
    return { ok: false, error: body as ErrorResponse };
  }
  return { ok: true, data: body as T };
}

// API-EDN-001: 財務データのダウンロード開始
export function startDownload(): Promise<ApiResult<{ status: string; message: string }>> {
  return requestJson("/api/download", { method: "POST" });
}

// API-EDN-002: ダウンロード進捗確認
export function getDownloadStatus(): Promise<ApiResult<DownloadStatus>> {
  return requestJson("/api/download/status");
}

// API-COM-001: 企業一覧取得
export function getCompanies(): Promise<ApiResult<Company[]>> {
  return requestJson("/api/companies");
}

// API-COM-002: 企業財務データ取得
export function getCompanyFinancials(code: string): Promise<ApiResult<CompanyFinancials>> {
  return requestJson(`/api/companies/${code}/financials`);
}
