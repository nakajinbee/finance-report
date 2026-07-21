import { useEffect, useRef, useState } from "react";
import { useNavigate } from "react-router-dom";
import {
  type EdinetCompanySearchResult,
  getDownloadStatus,
  searchEdinetCompanies,
  startDownload,
  type DownloadStatus,
} from "../api/client";
import { ErrorMessage } from "../components/ErrorMessage";

const POLL_INTERVAL_MS = 1000;
const SEARCH_DEBOUNCE_MS = 300;
const MAX_LOOKBACK_YEARS = 10;

const LOG_STATUS_ICON: Record<string, string> = {
  done: "✓",
  in_progress: "⏳",
  skipped: "→",
  error: "✗",
  pending: "・",
};

function secCodeToCompanyCode(secCode: string): string {
  return secCode.slice(0, 4);
}

export function DownloadPage() {
  const navigate = useNavigate();

  const [query, setQuery] = useState("");
  const [searchResults, setSearchResults] = useState<EdinetCompanySearchResult[]>([]);
  const [selectedCompany, setSelectedCompany] = useState<EdinetCompanySearchResult | null>(null);

  const [periodType, setPeriodType] = useState<"all" | "range">("all");
  const [fromYear, setFromYear] = useState(new Date().getFullYear() - 4);
  const [toYear, setToYear] = useState(new Date().getFullYear());

  const [isDownloading, setIsDownloading] = useState(false);
  const [status, setStatus] = useState<DownloadStatus | null>(null);
  const [submitError, setSubmitError] = useState<string | null>(null);
  const pollTimerRef = useRef<ReturnType<typeof setInterval> | null>(null);

  useEffect(() => {
    return () => {
      if (pollTimerRef.current) {
        clearInterval(pollTimerRef.current);
      }
    };
  }, []);

  // SCR-001-01: 企業検索ボックス。入力のたびにAPIを呼び出す（デバウンス要）
  useEffect(() => {
    if (selectedCompany !== null) {
      return;
    }
    const trimmed = query.trim();
    if (trimmed === "") {
      setSearchResults([]);
      return;
    }
    const timer = setTimeout(async () => {
      const result = await searchEdinetCompanies(trimmed);
      if (result.ok) {
        setSearchResults(result.data);
      }
    }, SEARCH_DEBOUNCE_MS);
    return () => clearTimeout(timer);
  }, [query, selectedCompany]);

  function selectCompany(company: EdinetCompanySearchResult) {
    setSelectedCompany(company);
    setSearchResults([]);
  }

  function clearSelection() {
    setSelectedCompany(null);
    setQuery("");
    setStatus(null);
    setSubmitError(null);
  }

  function pollStatus(companyCode: string) {
    pollTimerRef.current = setInterval(async () => {
      const result = await getDownloadStatus(companyCode);
      if (!result.ok) {
        return;
      }
      setStatus(result.data);
      if (result.data.status === "done" || result.data.status === "error") {
        setIsDownloading(false);
        if (pollTimerRef.current) {
          clearInterval(pollTimerRef.current);
          pollTimerRef.current = null;
        }
      }
    }, POLL_INTERVAL_MS);
  }

  async function handleDownloadClick() {
    if (selectedCompany === null || selectedCompany.sec_code === null) {
      return;
    }
    setSubmitError(null);
    setIsDownloading(true);
    setStatus(null);

    const companyCode = secCodeToCompanyCode(selectedCompany.sec_code);
    const result = await startDownload({
      company_code: companyCode,
      edinet_code: selectedCompany.edinet_code,
      period: periodType === "all" ? { type: "all" } : { type: "range", from_year: fromYear, to_year: toYear },
    });
    if (!result.ok) {
      // 409: すでにダウンロードが進行中。400: 期間指定が不正
      setSubmitError(result.error.message);
      setIsDownloading(false);
      return;
    }
    pollStatus(companyCode);
  }

  const hasAtLeastOneSuccess = status?.logs.some((log) => log.status === "done" || log.status === "skipped") ?? false;
  const showCompanyListLink = status?.status === "done" && hasAtLeastOneSuccess;
  const showAllFailedMessage = status?.status === "error";
  const canDownload = selectedCompany !== null && selectedCompany.sec_code !== null && !isDownloading;

  return (
    <div className="mx-auto max-w-xl space-y-6 p-8">
      <button type="button" onClick={() => navigate("/companies")} className="text-sm text-gray-500">
        ← 企業一覧へ
      </button>

      <h1 className="text-xl font-semibold">データ取得</h1>

      <div className="space-y-2">
        <p className="font-medium">対象企業：</p>
        {selectedCompany === null ? (
          <>
            <input
              type="text"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="企業名・証券コードで検索..."
              className="w-full rounded border border-gray-300 px-3 py-2"
            />
            {searchResults.length > 0 && (
              <ul className="divide-y divide-gray-100 rounded border border-gray-200">
                {searchResults.map((company) => (
                  <li key={company.edinet_code}>
                    <button
                      type="button"
                      onClick={() => selectCompany(company)}
                      className="w-full px-3 py-2 text-left hover:bg-gray-50"
                    >
                      <p>{company.name}</p>
                      <p className="text-sm text-gray-500">
                        {company.edinet_code} ｜ {company.sec_code ?? "証券コードなし"} ｜{" "}
                        {company.sector ?? "業種不明"}
                      </p>
                    </button>
                  </li>
                ))}
              </ul>
            )}
          </>
        ) : (
          <div className="flex items-center justify-between rounded border border-gray-300 px-3 py-2">
            <div>
              <p>選択中：{selectedCompany.name}</p>
              {selectedCompany.sec_code === null && (
                <p className="text-sm text-red-600">証券コードが不明なため、この企業はダウンロードできません</p>
              )}
            </div>
            <button type="button" onClick={clearSelection} className="text-sm text-gray-500">
              変更
            </button>
          </div>
        )}
      </div>

      <div className="space-y-2">
        <p className="font-medium">取得期間：</p>
        <label className="flex items-center gap-2">
          <input
            type="radio"
            checked={periodType === "all"}
            onChange={() => setPeriodType("all")}
          />
          全期間（最大{MAX_LOOKBACK_YEARS}年）
        </label>
        <label className="flex items-center gap-2">
          <input
            type="radio"
            checked={periodType === "range"}
            onChange={() => setPeriodType("range")}
          />
          期間指定
          <input
            type="number"
            value={fromYear}
            onChange={(e) => setFromYear(Number(e.target.value))}
            disabled={periodType !== "range"}
            className="w-20 rounded border border-gray-300 px-2 py-1 disabled:bg-gray-100"
          />
          年 〜
          <input
            type="number"
            value={toYear}
            onChange={(e) => setToYear(Number(e.target.value))}
            disabled={periodType !== "range"}
            className="w-20 rounded border border-gray-300 px-2 py-1 disabled:bg-gray-100"
          />
          年
        </label>
        {periodType === "all" && (
          <p className="text-sm text-gray-500">EDINETの制約により、実際に取得できるのは最大{MAX_LOOKBACK_YEARS}年分です</p>
        )}
      </div>

      <button
        type="button"
        onClick={handleDownloadClick}
        disabled={!canDownload}
        className="rounded bg-brand px-4 py-2 text-white hover:bg-brand-dark disabled:bg-gray-300"
      >
        データを取得する
      </button>

      {submitError && <ErrorMessage message={submitError} />}

      {status && status.logs.length > 0 && (
        <div className="space-y-1 border-t pt-4">
          <p className="font-medium">取得ログ：</p>
          <ul className="space-y-1">
            {status.logs.map((log, i) => (
              <li key={`${log.fiscal_year}-${i}`}>
                {LOG_STATUS_ICON[log.status]} {log.fiscal_year} {log.message}
              </li>
            ))}
          </ul>
        </div>
      )}

      {showAllFailedMessage && (
        <ErrorMessage message="データの取得に失敗しました。再度お試しください。" />
      )}

      {showCompanyListLink && (
        <button
          type="button"
          onClick={() => navigate("/companies")}
          className="rounded border border-gray-300 px-4 py-2"
        >
          企業一覧へ
        </button>
      )}
    </div>
  );
}
