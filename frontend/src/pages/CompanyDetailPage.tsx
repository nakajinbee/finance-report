import { useEffect, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import {
  getCompanyCashFlow,
  getCompanyFinancials,
  getCompanyQualitativeFacts,
  getCompanyRatios,
  type CashFlowRecord,
  type CompanyFinancials,
  type CompanyQualitativeFacts,
  type RatioRecord,
} from "../api/client";
import { Button } from "../components/Button";
import { CashFlowChart } from "../components/CashFlowChart";
import { CashFlowTable } from "../components/CashFlowTable";
import { ErrorMessage } from "../components/ErrorMessage";
import { FinancialMetricSection } from "../components/FinancialMetricSection";
import { Panel } from "../components/Panel";
import { QualitativeFactSection } from "../components/QualitativeFactSection";
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
  const [qualitativeFacts, setQualitativeFacts] = useState<CompanyQualitativeFacts | null>(null);
  const [selectedQualitativePeriod, setSelectedQualitativePeriod] = useState<string | undefined>(undefined);

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

  // 定性情報：財務グラフの年度範囲選択とは独立して取得する（サイクル13 FR-58）。
  // selectedQualitativePeriodが未選択（undefined）の間は最新年度を取得し、
  // レスポンスのperiod_endを初期選択値としてセットする
  useEffect(() => {
    if (!code) {
      return;
    }
    let cancelled = false;
    getCompanyQualitativeFacts(code, selectedQualitativePeriod).then((result) => {
      if (cancelled) {
        return;
      }
      if (result.ok) {
        setQualitativeFacts(result.data);
        if (selectedQualitativePeriod === undefined) {
          setSelectedQualitativePeriod(result.data.period_end);
        }
      } else {
        setQualitativeFacts(null);
      }
    });
    return () => {
      cancelled = true;
    };
  }, [code, selectedQualitativePeriod]);

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

      <div>
        <h1 className="text-xl font-semibold">{financials.company.name}</h1>
        <p className="text-gray-500">
          会計基準：{financials.company.accounting_standard ?? "データ未取得"} ｜{" "}
          {financials.company.sector ?? "業種不明"}
        </p>
        {financials.company.sector !== null && (
          <button
            type="button"
            onClick={() =>
              navigate(`/ranking?sector=${encodeURIComponent(financials.company.sector ?? "")}`)
            }
            className="text-sm text-brand hover:text-brand-dark"
          >
            この企業の業種内での順位を見る →
          </button>
        )}
      </div>

      {availableYears.length > 0 && fromYear !== null && toYear !== null && (
        <div className="flex items-center gap-2">
          <span className="font-medium">表示期間：</span>
          <select
            value={fromYear}
            onChange={(e) => setFromYear(Number(e.target.value))}
            className="rounded border border-gray-300 px-2 py-1 outline-none focus:border-brand focus:ring-2 focus:ring-brand/20"
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
            className="rounded border border-gray-300 px-2 py-1 outline-none focus:border-brand focus:ring-2 focus:ring-brand/20"
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

      {financials.data.length > 0 ? (
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
      ) : (
        <Panel className="space-y-3 text-center">
          <p className="text-gray-500">まだ財務データを取得していません</p>
          <Button onClick={() => navigate("/download")}>
            データを取得する
          </Button>
        </Panel>
      )}

      <Panel className="space-y-3">
        <div className="flex items-center justify-between">
          <h2 className="text-lg font-semibold text-gray-900">事業概要・リスク</h2>
          {qualitativeFacts && (
            <label className="flex items-center gap-2 text-sm">
              年度：
              <select
                value={selectedQualitativePeriod ?? qualitativeFacts.period_end}
                onChange={(e) => setSelectedQualitativePeriod(e.target.value)}
                className="rounded border border-gray-300 px-2 py-1 outline-none focus:border-brand focus:ring-2 focus:ring-brand/20"
              >
                {qualitativeFacts.available_periods.map((period) => (
                  <option key={period} value={period}>
                    {period}
                  </option>
                ))}
              </select>
            </label>
          )}
        </div>
        {!qualitativeFacts ? (
          <p className="text-gray-500">事業概要・リスク情報はありません</p>
        ) : qualitativeFacts.business_description === null &&
          qualitativeFacts.business_risks === null &&
          qualitativeFacts.mdanda === null ? (
          <p className="text-gray-500">この年度の事業概要・リスク情報はありません</p>
        ) : (
          <div>
            <QualitativeFactSection title="事業の内容" content={qualitativeFacts.business_description} />
            <QualitativeFactSection title="事業等のリスク" content={qualitativeFacts.business_risks} />
            <QualitativeFactSection title="経営者による分析（MD&A）" content={qualitativeFacts.mdanda} />
          </div>
        )}
      </Panel>
    </div>
  );
}
