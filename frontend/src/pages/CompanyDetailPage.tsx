import { useEffect, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import {
  getCompanyCashFlow,
  getCompanyFinancials,
  getCompanyRatios,
  type CashFlowRecord,
  type CompanyFinancials,
  type RatioRecord,
} from "../api/client";
import { Button } from "../components/Button";
import { CashFlowChart } from "../components/CashFlowChart";
import { CashFlowTable } from "../components/CashFlowTable";
import { ErrorMessage } from "../components/ErrorMessage";
import { FinancialMetricSection } from "../components/FinancialMetricSection";
import { Panel } from "../components/Panel";
import { RatioCategorySection } from "../components/RatioCategorySection";
import { BS_METRIC_DEFINITIONS, PL_METRIC_DEFINITIONS } from "../lib/metrics";
import {
  EFFICIENCY_RATIOS,
  INVESTMENT_RATIOS,
  PROFITABILITY_RATIOS,
  SAFETY_RATIOS,
} from "../lib/ratioCategories";

type LoadState = "loading" | "loaded" | "not_found" | "error";

function yearsFromPeriods(periods: string[]): number[] {
  return Array.from(new Set(periods.map((p) => Number(p.slice(0, 4))))).sort(
    (a, b) => a - b,
  );
}

export function CompanyDetailPage() {
  const { code } = useParams<{ code: string }>();
  const navigate = useNavigate();

  const [loadState, setLoadState] = useState<LoadState>("loading");
  const [financials, setFinancials] = useState<CompanyFinancials | null>(null);
  const [cashFlow, setCashFlow] = useState<CashFlowRecord[]>([]);
  const [ratios, setRatios] = useState<RatioRecord[]>([]);
  const [availableYears, setAvailableYears] = useState<number[]>([]);
  const [fromYear, setFromYear] = useState<number | null>(null);
  const [toYear, setToYear] = useState<number | null>(null);

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
    Promise.all([
      getCompanyFinancials(code, fromYear, toYear),
      getCompanyCashFlow(code, fromYear, toYear),
      getCompanyRatios(code, fromYear, toYear),
    ]).then(([financialsResult, cashFlowResult, ratiosResult]) => {
      if (cancelled) {
        return;
      }
      if (financialsResult.ok) {
        setFinancials(financialsResult.data);
        setCashFlow(cashFlowResult.ok ? cashFlowResult.data : []);
        setRatios(ratiosResult.ok ? ratiosResult.data : []);
        setLoadState("loaded");
      } else if (financialsResult.error.error === "COMPANY_NOT_FOUND") {
        setLoadState("not_found");
      } else {
        setLoadState("error");
      }
    });
    return () => {
      cancelled = true;
    };
  }, [code, fromYear, toYear]);

  if (loadState === "loading") {
    return (
      <div className="flex justify-center py-16 text-gray-500">
        データを読み込んでいます...
      </div>
    );
  }

  if (loadState === "not_found" || loadState === "error") {
    return (
      <div className="mx-auto max-w-2xl p-8">
        <ErrorMessage message="データの取得に失敗しました。しばらくしてから再度お試しください。" />
      </div>
    );
  }

  if (!financials) {
    return null;
  }

  return (
    <div className="mx-auto max-w-6xl space-y-6 p-8">
      <button
        type="button"
        onClick={() => navigate("/companies")}
        className="text-sm text-gray-500"
      >
        ← 企業一覧へ
      </button>

      <div className="flex items-start justify-between">
        <div>
          <h1 className="text-xl font-semibold">{financials.company.name}</h1>
          <p className="text-gray-500">
            会計基準：{financials.company.accounting_standard}
          </p>
        </div>
        {code && (
          <Button
            variant="secondary"
            onClick={() => navigate(`/companies/${code}/facts`)}
          >
            生データを確認
          </Button>
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

      {financials.data.length > 0 && (
        <>
          <div className="grid grid-cols-1 gap-6 xl:grid-cols-2">
            <FinancialMetricSection
              title="貸借対照表（B/S）"
              records={financials.data}
              definitions={BS_METRIC_DEFINITIONS}
            />
            <FinancialMetricSection
              title="損益計算書（P/L）"
              records={financials.data}
              definitions={PL_METRIC_DEFINITIONS}
            />
          </div>

          <Panel className="space-y-3">
            <h2 className="text-lg font-semibold text-gray-900">
              キャッシュフロー計算書
            </h2>
            <CashFlowChart records={cashFlow} />
            <CashFlowTable
              financialRecords={financials.data}
              cashFlowRecords={cashFlow}
            />
          </Panel>

          <div className="space-y-4">
            <h2 className="text-lg font-semibold text-gray-900">
              財務分析指標
            </h2>
            <div className="grid grid-cols-1 gap-6 xl:grid-cols-2">
              <RatioCategorySection
                title="収益性"
                financialRecords={financials.data}
                ratioRecords={ratios}
                definitions={PROFITABILITY_RATIOS}
              />
              <RatioCategorySection
                title="効率性"
                financialRecords={financials.data}
                ratioRecords={ratios}
                definitions={EFFICIENCY_RATIOS}
              />
              <RatioCategorySection
                title="安全性"
                financialRecords={financials.data}
                ratioRecords={ratios}
                definitions={SAFETY_RATIOS}
              />
              <RatioCategorySection
                title="投資指標"
                financialRecords={financials.data}
                ratioRecords={ratios}
                definitions={INVESTMENT_RATIOS}
              />
            </div>
          </div>
        </>
      )}
    </div>
  );
}
