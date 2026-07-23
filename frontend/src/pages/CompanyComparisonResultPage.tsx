import { useEffect, useState } from "react";
import { useNavigate, useSearchParams } from "react-router-dom";
import {
  getCompanyCashFlow,
  getCompanyFinancials,
  getCompanyRatios,
  type CashFlowRecord,
  type Company,
  type FinancialRecord,
  type RatioRecord,
} from "../api/client";
import { Button } from "../components/Button";
import { ComparisonMoneyChart } from "../components/comparison/ComparisonMoneyChart";
import { ComparisonMoneyTable } from "../components/comparison/ComparisonMoneyTable";
import { ComparisonRatioChart } from "../components/comparison/ComparisonRatioChart";
import { ComparisonRatioTable } from "../components/comparison/ComparisonRatioTable";
import { Panel } from "../components/Panel";
import { BS_METRIC_DEFINITIONS, PL_METRIC_DEFINITIONS } from "../lib/metrics";
import {
  EFFICIENCY_RATIOS,
  INVESTMENT_RATIOS,
  PROFITABILITY_RATIOS,
  SAFETY_RATIOS,
} from "../lib/ratioCategories";

type LoadState = "loading" | "loaded";

type CompanyResult = {
  company: Company;
  financial: FinancialRecord | null;
  cashFlow: CashFlowRecord | null;
  ratio: RatioRecord | null;
  failed: boolean;
};

function latest<T extends { period_end: string }>(records: T[]): T | null {
  if (records.length === 0) {
    return null;
  }
  return records.reduce((a, b) => (a.period_end > b.period_end ? a : b));
}

const CF_METRICS = [
  { key: "operating_cash_flow", label: "営業CF", color: "#1F3864" },
  { key: "investing_cash_flow", label: "投資CF", color: "#6699CC" },
  { key: "financing_cash_flow", label: "財務CF", color: "#F28E2B" },
];

// SCR-006 比較結果画面（サイクル15新規）。SCR-005で選択した企業（クエリパラメータ`codes`）
// について、SCR-003と同じカテゴリ構成で企業別の棒グラフ・表を表示する。
export function CompanyComparisonResultPage() {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const codes = (searchParams.get("codes") ?? "")
    .split(",")
    .map((c) => c.trim())
    .filter((c) => c !== "");

  const [loadState, setLoadState] = useState<LoadState>("loading");
  const [results, setResults] = useState<CompanyResult[]>([]);

  useEffect(() => {
    if (codes.length === 0) {
      setResults([]);
      setLoadState("loaded");
      return;
    }
    let cancelled = false;
    setLoadState("loading");
    Promise.all(
      codes.map(async (code) => {
        const [financialsResult, cashFlowResult, ratiosResult] = await Promise.all([
          getCompanyFinancials(code),
          getCompanyCashFlow(code),
          getCompanyRatios(code),
        ]);
        if (!financialsResult.ok) {
          return { failed: true as const, code };
        }
        return {
          failed: false as const,
          company: financialsResult.data.company,
          financial: latest(financialsResult.data.data),
          cashFlow: cashFlowResult.ok ? latest(cashFlowResult.data) : null,
          ratio: ratiosResult.ok ? latest(ratiosResult.data) : null,
        };
      }),
    ).then((items) => {
      if (cancelled) {
        return;
      }
      const succeeded: CompanyResult[] = items
        .filter((item): item is Exclude<typeof item, { failed: true }> => !item.failed)
        .map((item) => ({
          company: item.company,
          financial: item.financial,
          cashFlow: item.cashFlow,
          ratio: item.ratio,
          failed: false,
        }));
      setResults(succeeded);
      setLoadState("loaded");
    });
    return () => {
      cancelled = true;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [searchParams.get("codes")]);

  if (loadState === "loading") {
    return <div className="flex justify-center py-16 text-gray-500">データを読み込んでいます...</div>;
  }

  if (results.length === 0) {
    return (
      <div className="mx-auto max-w-2xl space-y-4 p-8 text-center">
        <p className="text-gray-500">比較する企業が選択されていません</p>
        <Button variant="secondary" onClick={() => navigate("/compare")}>
          比較する企業を選ぶ
        </Button>
      </div>
    );
  }

  const failedCount = codes.length - results.length;

  const financialData = results.map((r) => ({
    code: r.company.code,
    name: r.company.name,
    ...(r.financial ?? {}),
  }));
  const cashFlowData = results.map((r) => ({
    code: r.company.code,
    name: r.company.name,
    ...(r.cashFlow ?? {}),
  }));
  const ratioData = results.map((r) => ({
    code: r.company.code,
    name: r.company.name,
    ...(r.ratio ?? {}),
  }));

  function goToCompany(code: string) {
    navigate(`/companies/${code}`);
  }

  return (
    <div className="mx-auto max-w-6xl space-y-6 p-8">
      <button type="button" onClick={() => navigate("/compare")} className="text-sm text-gray-500">
        ← 比較する企業を選び直す
      </button>

      <h1 className="text-xl font-semibold">比較結果（{results.length}社）</h1>

      {failedCount > 0 && (
        <p className="text-sm text-red-600">
          一部の企業のデータ取得に失敗しました（{failedCount}社）
        </p>
      )}

      <div className="grid grid-cols-1 gap-6 xl:grid-cols-2">
        <Panel className="space-y-3">
          <h2 className="text-lg font-semibold text-gray-900">貸借対照表（B/S）</h2>
          <ComparisonMoneyChart data={financialData} metrics={BS_METRIC_DEFINITIONS} />
          <ComparisonMoneyTable data={financialData} metrics={BS_METRIC_DEFINITIONS} onCompanyClick={goToCompany} />
        </Panel>
        <Panel className="space-y-3">
          <h2 className="text-lg font-semibold text-gray-900">損益計算書（P/L）</h2>
          <ComparisonMoneyChart data={financialData} metrics={PL_METRIC_DEFINITIONS} />
          <ComparisonMoneyTable data={financialData} metrics={PL_METRIC_DEFINITIONS} onCompanyClick={goToCompany} />
        </Panel>
      </div>

      <Panel className="space-y-3">
        <h2 className="text-lg font-semibold text-gray-900">キャッシュフロー計算書</h2>
        <ComparisonMoneyChart data={cashFlowData} metrics={CF_METRICS} />
        <ComparisonMoneyTable data={cashFlowData} metrics={CF_METRICS} onCompanyClick={goToCompany} />
      </Panel>

      <div className="space-y-4">
        <h2 className="text-lg font-semibold text-gray-900">財務分析指標</h2>
        <div className="grid grid-cols-1 gap-6 xl:grid-cols-2">
          <Panel className="space-y-2">
            <h3 className="font-medium">収益性</h3>
            <ComparisonRatioChart data={ratioData} metrics={PROFITABILITY_RATIOS} />
            <ComparisonRatioTable data={ratioData} metrics={PROFITABILITY_RATIOS} onCompanyClick={goToCompany} />
          </Panel>
          <Panel className="space-y-2">
            <h3 className="font-medium">効率性</h3>
            <ComparisonRatioChart data={ratioData} metrics={EFFICIENCY_RATIOS} />
            <ComparisonRatioTable data={ratioData} metrics={EFFICIENCY_RATIOS} onCompanyClick={goToCompany} />
          </Panel>
          <Panel className="space-y-2">
            <h3 className="font-medium">安全性</h3>
            <ComparisonRatioChart data={ratioData} metrics={SAFETY_RATIOS} />
            <ComparisonRatioTable data={ratioData} metrics={SAFETY_RATIOS} onCompanyClick={goToCompany} />
          </Panel>
          <Panel className="space-y-2">
            <h3 className="font-medium">投資指標</h3>
            <ComparisonRatioChart data={ratioData} metrics={INVESTMENT_RATIOS} />
            <ComparisonRatioTable data={ratioData} metrics={INVESTMENT_RATIOS} onCompanyClick={goToCompany} />
          </Panel>
        </div>
      </div>
    </div>
  );
}
