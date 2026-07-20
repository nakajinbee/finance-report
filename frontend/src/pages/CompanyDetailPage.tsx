import { useEffect, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import {
  getCompanyCashFlow,
  getCompanyFinancials,
  type CashFlowRecord,
  type CompanyFinancials,
} from "../api/client";
import { CashFlowChart } from "../components/CashFlowChart";
import { CashFlowTable } from "../components/CashFlowTable";
import { ErrorMessage } from "../components/ErrorMessage";
import { FinancialChart } from "../components/FinancialChart";
import { MetricSelector } from "../components/MetricSelector";
import { METRIC_DEFINITIONS, type MetricKey } from "../lib/metrics";

type LoadState = "loading" | "loaded" | "not_found" | "error";

function yearsFromPeriods(periods: string[]): number[] {
  return Array.from(new Set(periods.map((p) => Number(p.slice(0, 4))))).sort((a, b) => a - b);
}

export function CompanyDetailPage() {
  const { code } = useParams<{ code: string }>();
  const navigate = useNavigate();

  const [loadState, setLoadState] = useState<LoadState>("loading");
  const [financials, setFinancials] = useState<CompanyFinancials | null>(null);
  const [cashFlow, setCashFlow] = useState<CashFlowRecord[]>([]);
  const [availableYears, setAvailableYears] = useState<number[]>([]);
  const [fromYear, setFromYear] = useState<number | null>(null);
  const [toYear, setToYear] = useState<number | null>(null);
  const [activeMetrics, setActiveMetrics] = useState<Set<MetricKey>>(
    () => new Set(METRIC_DEFINITIONS.map((m) => m.key)),
  );

  // 初回ロード：保存済みの全期間を取得し、年度選択の選択肢と初期選択（全期間）を決める
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
        const years = yearsFromPeriods(result.data.company.periods);
        setAvailableYears(years);
        if (years.length > 0) {
          setFromYear(years[0]);
          setToYear(years[years.length - 1]);
        } else {
          setFinancials(result.data);
          setLoadState("loaded");
        }
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

  // 表示期間選択（開始年度・終了年度）が決まるたびに、財務データ・キャッシュフローを再取得する
  useEffect(() => {
    if (!code || fromYear === null || toYear === null) {
      return;
    }
    let cancelled = false;
    setLoadState((current) => (current === "loaded" ? current : "loading"));
    Promise.all([getCompanyFinancials(code, fromYear, toYear), getCompanyCashFlow(code, fromYear, toYear)]).then(
      ([financialsResult, cashFlowResult]) => {
        if (cancelled) {
          return;
        }
        if (financialsResult.ok) {
          setFinancials(financialsResult.data);
          setCashFlow(cashFlowResult.ok ? cashFlowResult.data : []);
          setLoadState("loaded");
        } else if (financialsResult.error.error === "COMPANY_NOT_FOUND") {
          setLoadState("not_found");
        } else {
          setLoadState("error");
        }
      },
    );
    return () => {
      cancelled = true;
    };
  }, [code, fromYear, toYear]);

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

  const hasAnyValue = financials.data.some((record) =>
    METRIC_DEFINITIONS.some((metric) => record[metric.key] !== null),
  );

  return (
    <div className="mx-auto max-w-3xl space-y-6 p-8">
      <button type="button" onClick={() => navigate("/companies")} className="text-sm text-gray-500">
        ← 企業一覧へ
      </button>

      <div className="flex items-start justify-between">
        <div>
          <h1 className="text-xl font-semibold">{financials.company.name}</h1>
          <p className="text-gray-500">会計基準：{financials.company.accounting_standard}</p>
        </div>
        {code && (
          <button
            type="button"
            onClick={() => navigate(`/companies/${code}/facts`)}
            className="text-sm text-gray-500 underline"
          >
            生データを確認
          </button>
        )}
      </div>

      {availableYears.length > 0 && fromYear !== null && toYear !== null && (
        <div className="flex items-center gap-2">
          <span className="font-medium">表示期間：</span>
          <select
            value={fromYear}
            onChange={(e) => setFromYear(Number(e.target.value))}
            className="rounded border border-gray-300 px-2 py-1"
          >
            {availableYears
              .filter((year) => year <= toYear)
              .map((year) => (
                <option key={year} value={year}>
                  {year}年
                </option>
              ))}
          </select>
          〜
          <select
            value={toYear}
            onChange={(e) => setToYear(Number(e.target.value))}
            className="rounded border border-gray-300 px-2 py-1"
          >
            {availableYears
              .filter((year) => year >= fromYear)
              .map((year) => (
                <option key={year} value={year}>
                  {year}年
                </option>
              ))}
          </select>
        </div>
      )}

      <MetricSelector activeMetrics={activeMetrics} onToggle={toggleMetric} />

      {activeMetrics.size === 0 ? (
        <p className="text-gray-500">指標を1つ以上選択してください</p>
      ) : !hasAnyValue ? (
        <p className="text-gray-500">表示できるデータがありません</p>
      ) : (
        <FinancialChart records={financials.data} activeMetrics={activeMetrics} />
      )}

      {financials.data.length > 0 && (
        <div className="space-y-2">
          <h2 className="font-medium">キャッシュフロー計算書</h2>
          <CashFlowChart records={cashFlow} />
          <CashFlowTable financialRecords={financials.data} cashFlowRecords={cashFlow} />
        </div>
      )}
    </div>
  );
}
