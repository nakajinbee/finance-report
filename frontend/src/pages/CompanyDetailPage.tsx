import { useEffect, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { getCompanyFinancials, type CompanyFinancials } from "../api/client";
import { ErrorMessage } from "../components/ErrorMessage";
import { FinancialChart } from "../components/FinancialChart";
import { MetricSelector } from "../components/MetricSelector";
import { METRIC_DEFINITIONS, type MetricKey } from "../lib/metrics";

type LoadState = "loading" | "loaded" | "not_found" | "error";

const PERIOD_OPTIONS = [3, 5, 10] as const;
const DEFAULT_PERIOD_COUNT = 5;

export function CompanyDetailPage() {
  const { code } = useParams<{ code: string }>();
  const navigate = useNavigate();
  const [financials, setFinancials] = useState<CompanyFinancials | null>(null);
  const [loadState, setLoadState] = useState<LoadState>("loading");
  const [periodCount, setPeriodCount] = useState<number>(DEFAULT_PERIOD_COUNT);
  const [activeMetrics, setActiveMetrics] = useState<Set<MetricKey>>(
    () => new Set(METRIC_DEFINITIONS.map((m) => m.key)),
  );

  useEffect(() => {
    if (!code) {
      return;
    }
    let cancelled = false;
    getCompanyFinancials(code).then((result) => {
      if (cancelled) {
        return;
      }
      if (result.ok) {
        setFinancials(result.data);
        setLoadState("loaded");
      } else if (result.error.error === "COMPANY_NOT_FOUND") {
        setLoadState("not_found");
      } else {
        setLoadState("error");
      }
    });
    return () => {
      cancelled = true;
    };
  }, [code]);

  function toggleMetric(key: MetricKey) {
    setActiveMetrics((current) => {
      const next = new Set(current);
      if (next.has(key)) {
        next.delete(key);
      } else {
        next.add(key);
      }
      return next;
    });
  }

  if (loadState === "loading") {
    return <p className="p-8">データを読み込んでいます...</p>;
  }

  if (loadState === "not_found" || loadState === "error") {
    return (
      <div className="p-8">
        <ErrorMessage message="データの取得に失敗しました。しばらくしてから再度お試しください。" />
      </div>
    );
  }

  if (!financials) {
    return null;
  }

  // dataはperiod_end昇順（API-COM-002）。直近N期分＝末尾からN件を取り、時系列順は維持する
  const visibleRecords = financials.data.slice(-periodCount);
  const hasAnyValue = visibleRecords.some((record) =>
    METRIC_DEFINITIONS.some((metric) => record[metric.key] !== null),
  );

  return (
    <div className="mx-auto max-w-3xl space-y-6 p-8">
      <button type="button" onClick={() => navigate("/companies")} className="text-sm text-gray-500">
        ← 企業一覧へ
      </button>

      <div>
        <h1 className="text-xl font-semibold">{financials.company.name}</h1>
        <p className="text-gray-500">会計基準：{financials.company.accounting_standard}</p>
      </div>

      <div className="flex gap-2">
        {PERIOD_OPTIONS.map((count) => (
          <button
            key={count}
            type="button"
            onClick={() => setPeriodCount(count)}
            className={`rounded border px-3 py-1.5 text-sm ${
              periodCount === count ? "border-gray-400 bg-gray-100" : "border-gray-200"
            }`}
          >
            {count}期
          </button>
        ))}
      </div>

      <MetricSelector activeMetrics={activeMetrics} onToggle={toggleMetric} />

      {activeMetrics.size === 0 ? (
        <p className="text-gray-500">指標を1つ以上選択してください</p>
      ) : !hasAnyValue ? (
        <p className="text-gray-500">表示できるデータがありません</p>
      ) : (
        <FinancialChart records={visibleRecords} activeMetrics={activeMetrics} />
      )}
    </div>
  );
}
