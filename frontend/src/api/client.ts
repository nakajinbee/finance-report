// docs/design/api/openapi.yaml のスキーマ名と1対1になる型定義。
// APIのベースURLは開発用の固定値（秘密情報ではないため .env 化はしない）。
const API_BASE_URL = "http://localhost:8000";

export type Company = {
  code: string;
  name: string;
  sector: string | null;
  accounting_standard: string | null;
  periods: string[]; // ISO date文字列（YYYY-MM-DD、docs/development/date_format_policy.md準拠）
};

export type FinancialRecord = {
  fiscal_year: string;
  period_end: string;
  revenue: number | null;
  operating_profit: number | null;
  ordinary_profit: number | null;
  net_profit: number | null;
  total_assets: number | null;
  total_liabilities: number | null;
  equity: number | null;
};

export type CompanyFinancials = {
  company: Company;
  data: FinancialRecord[];
};

export type CashFlowRecord = {
  fiscal_year: string;
  period_end: string;
  operating_cash_flow: number | null;
  investing_cash_flow: number | null;
  financing_cash_flow: number | null;
};

export type RatioRecord = {
  fiscal_year: string;
  period_end: string;
  roe: number | null;
  equity_ratio: number | null;
  eps: number | null;
  per: number | null;
  payout_ratio: number | null;
  roa: number | null;
  total_asset_turnover: number | null;
  operating_margin: number | null;
  net_margin: number | null;
  current_ratio: number | null;
  fixed_ratio: number | null;
  inventory_turnover: number | null;
  current_assets: number | null;
  current_liabilities: number | null;
  non_current_assets: number | null;
  non_current_liabilities: number | null;
  inventories: number | null;
};

export type CompanyQualitativeFacts = {
  period_end: string;
  available_periods: string[];
  business_description: string | null;
  business_risks: string | null;
  mdanda: string | null;
};

export type DownloadLogStatus = "pending" | "in_progress" | "done" | "skipped" | "error";

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

export type EdinetCompanySearchResult = {
  edinet_code: string;
  name: string;
  sec_code: string | null;
  sector: string | null;
};

export type DownloadPeriod =
  | { type: "all" }
  | { type: "range"; from_year: number; to_year: number };

export type DownloadRequest = {
  company_code: string;
  edinet_code: string;
  period: DownloadPeriod;
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

function buildQuery(params: Record<string, string | number | undefined>): string {
  const search = new URLSearchParams();
  for (const [key, value] of Object.entries(params)) {
    if (value !== undefined) {
      search.set(key, String(value));
    }
  }
  const query = search.toString();
  return query ? `?${query}` : "";
}

// API-EDN-001: 財務データのダウンロード開始
export function startDownload(request: DownloadRequest): Promise<ApiResult<{ status: string; message: string }>> {
  return requestJson("/api/download", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(request),
  });
}

// API-EDN-002: ダウンロード進捗確認
export function getDownloadStatus(companyCode: string): Promise<ApiResult<DownloadStatus>> {
  return requestJson(`/api/download/status${buildQuery({ company_code: companyCode })}`);
}

// API-EDN-003: EDINET企業検索
export function searchEdinetCompanies(q: string): Promise<ApiResult<EdinetCompanySearchResult[]>> {
  return requestJson(`/api/edinet/companies/search${buildQuery({ q })}`);
}

// API-COM-001: 企業一覧取得
export function getCompanies(): Promise<ApiResult<Company[]>> {
  return requestJson("/api/companies");
}

// API-COM-002: 企業財務データ取得
export function getCompanyFinancials(
  code: string,
  fromYear?: number,
  toYear?: number,
): Promise<ApiResult<CompanyFinancials>> {
  return requestJson(`/api/companies/${code}/financials${buildQuery({ from_year: fromYear, to_year: toYear })}`);
}

// API-COM-003: 企業キャッシュフロー取得
export function getCompanyCashFlow(
  code: string,
  fromYear?: number,
  toYear?: number,
): Promise<ApiResult<CashFlowRecord[]>> {
  return requestJson(`/api/companies/${code}/cashflow${buildQuery({ from_year: fromYear, to_year: toYear })}`);
}

// API-COM-005: 企業財務分析指標取得
export function getCompanyRatios(
  code: string,
  fromYear?: number,
  toYear?: number,
): Promise<ApiResult<RatioRecord[]>> {
  return requestJson(`/api/companies/${code}/ratios${buildQuery({ from_year: fromYear, to_year: toYear })}`);
}

// API-COM-006: 企業の定性データ取得（サイクル13新規）
export function getCompanyQualitativeFacts(
  code: string,
  periodEnd?: string,
): Promise<ApiResult<CompanyQualitativeFacts>> {
  return requestJson(`/api/companies/${code}/qualitative-facts${buildQuery({ period_end: periodEnd })}`);
}
