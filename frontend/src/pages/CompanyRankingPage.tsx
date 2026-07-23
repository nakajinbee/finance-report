import { useEffect, useState } from "react";
import { useNavigate, useSearchParams } from "react-router-dom";
import { getCompanies, getCompanyRanking, type Company, type RankingMetric, type RankingRecord } from "../api/client";
import { Button } from "../components/Button";
import { formatYenForDisplay } from "../lib/formatCurrency";
import { formatByRatioFormat } from "../lib/formatRatio";
import { ALL_SECTORS } from "../lib/useCompanyFilter";

type SortDirection = "desc" | "asc";

const METRIC_OPTIONS: { value: RankingMetric; label: string; kind: "money" | "percent" | "turnover" | "number" }[] = [
  { value: "revenue", label: "売上高", kind: "money" },
  { value: "operating_profit", label: "営業利益", kind: "money" },
  { value: "ordinary_profit", label: "経常利益", kind: "money" },
  { value: "net_profit", label: "純利益", kind: "money" },
  { value: "total_assets", label: "総資産", kind: "money" },
  { value: "total_liabilities", label: "負債", kind: "money" },
  { value: "equity", label: "自己資本（純資産）", kind: "money" },
  { value: "roe", label: "ROE（自己資本利益率）", kind: "percent" },
  { value: "equity_ratio", label: "自己資本比率", kind: "percent" },
  { value: "eps", label: "EPS（1株当たり当期純利益）", kind: "number" },
  { value: "per", label: "PER（株価収益率）", kind: "number" },
  { value: "payout_ratio", label: "配当性向", kind: "percent" },
  { value: "roa", label: "ROA（総資産利益率）", kind: "percent" },
  { value: "total_asset_turnover", label: "総資産回転率", kind: "turnover" },
  { value: "operating_margin", label: "売上高営業利益率", kind: "percent" },
  { value: "net_margin", label: "売上高純利益率", kind: "percent" },
  { value: "current_ratio", label: "流動比率", kind: "percent" },
  { value: "fixed_ratio", label: "固定比率", kind: "percent" },
  { value: "inventory_turnover", label: "棚卸資産回転率", kind: "turnover" },
];

function formatValue(value: number, kind: "money" | "percent" | "turnover" | "number"): string {
  if (kind === "money") {
    return formatYenForDisplay(value);
  }
  if (kind === "percent") {
    return formatByRatioFormat(value, "percent");
  }
  if (kind === "turnover") {
    return formatByRatioFormat(value, "turnover");
  }
  return formatByRatioFormat(value, "number");
}

type LoadState = "idle" | "loading" | "loaded" | "error";

type AppliedQuery = { metric: RankingMetric; sector: string };

// SCR-007 ランキング画面（サイクル15新規）。SCR-003から遷移した場合、`sector`クエリパラメータで
// 業種を引き継ぐ。指標・業種の選択自体は即座に反映されるが、実際のデータ取得は
// 「表示」ボタンを押したときのみ行う（2026-07-24訂正：指標を選んだ瞬間に業種すべての
// データが表示されてしまうというユーザー指摘を受けて変更）。
export function CompanyRankingPage() {
  const navigate = useNavigate();
  const [searchParams, setSearchParams] = useSearchParams();
  const [companies, setCompanies] = useState<Company[]>([]);
  const [metric, setMetric] = useState<RankingMetric | "">("");
  const [sector, setSector] = useState(searchParams.get("sector") ?? ALL_SECTORS);
  const [direction, setDirection] = useState<SortDirection>("desc");
  const [records, setRecords] = useState<RankingRecord[]>([]);
  const [loadState, setLoadState] = useState<LoadState>("idle");
  const [appliedQuery, setAppliedQuery] = useState<AppliedQuery | null>(null);

  useEffect(() => {
    getCompanies().then((result) => {
      if (result.ok) {
        setCompanies(result.data);
      }
    });
  }, []);

  useEffect(() => {
    if (appliedQuery === null) {
      setLoadState("idle");
      return;
    }
    let cancelled = false;
    setLoadState("loading");
    getCompanyRanking(
      appliedQuery.metric,
      appliedQuery.sector === ALL_SECTORS ? undefined : appliedQuery.sector,
    ).then((result) => {
      if (cancelled) {
        return;
      }
      if (result.ok) {
        setRecords(result.data);
        setLoadState("loaded");
      } else {
        setLoadState("error");
      }
    });
    return () => {
      cancelled = true;
    };
  }, [appliedQuery]);

  function handleShow() {
    if (metric === "") {
      return;
    }
    setAppliedQuery({ metric, sector });
  }

  const sectorOptions = Array.from(
    new Set(companies.map((c) => c.sector).filter((v): v is string => v !== null)),
  ).sort((a, b) => a.localeCompare(b, "ja"));

  const sortedRecords = [...records].sort((a, b) =>
    direction === "desc" ? b.value - a.value : a.value - b.value,
  );

  const metricOption = appliedQuery ? METRIC_OPTIONS.find((m) => m.value === appliedQuery.metric) : undefined;

  return (
    <div className="mx-auto max-w-4xl space-y-4 p-8">
      <h1 className="text-xl font-semibold">ランキング</h1>

      <div className="flex gap-3">
        <select
          value={metric}
          onChange={(e) => setMetric(e.target.value as RankingMetric | "")}
          className="rounded border border-gray-300 px-3 py-2 outline-none focus:border-brand focus:ring-2 focus:ring-brand/20"
        >
          <option value="">指標を選択...</option>
          {METRIC_OPTIONS.map((option) => (
            <option key={option.value} value={option.value}>
              {option.label}
            </option>
          ))}
        </select>

        <select
          value={sector}
          onChange={(e) => {
            setSector(e.target.value);
            setSearchParams(e.target.value === ALL_SECTORS ? {} : { sector: e.target.value });
          }}
          className="rounded border border-gray-300 px-3 py-2 outline-none focus:border-brand focus:ring-2 focus:ring-brand/20"
        >
          <option value={ALL_SECTORS}>業種：すべて</option>
          {sectorOptions.map((option) => (
            <option key={option} value={option}>
              {option}
            </option>
          ))}
        </select>

        <select
          value={direction}
          onChange={(e) => setDirection(e.target.value as SortDirection)}
          className="rounded border border-gray-300 px-3 py-2 outline-none focus:border-brand focus:ring-2 focus:ring-brand/20"
        >
          <option value="desc">降順</option>
          <option value="asc">昇順</option>
        </select>

        <Button variant="primary" disabled={metric === ""} onClick={handleShow}>
          表示
        </Button>
      </div>

      {loadState === "idle" && (
        <p className="text-sm text-gray-500">指標・業種を選んで「表示」を押してください</p>
      )}

      {loadState === "loading" && (
        <div className="flex justify-center py-16 text-gray-500">データを読み込んでいます...</div>
      )}

      {loadState === "error" && (
        <p className="text-red-600">データの取得に失敗しました。しばらくしてから再度お試しください。</p>
      )}

      {loadState === "loaded" && metricOption && (
        sortedRecords.length === 0 ? (
          <p className="text-gray-500">該当するデータがありません</p>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="bg-gray-50">
                  <th className="border-b border-gray-200 px-3 py-2 text-left">順位</th>
                  <th className="border-b border-gray-200 px-3 py-2 text-left">企業名</th>
                  <th className="border-b border-gray-200 px-3 py-2 text-left">証券コード</th>
                  <th className="border-b border-gray-200 px-3 py-2 text-left">業種</th>
                  <th className="border-b border-gray-200 px-3 py-2 text-right">{metricOption.label}</th>
                </tr>
              </thead>
              <tbody>
                {sortedRecords.map((record, index) => (
                  <tr
                    key={record.code}
                    className="cursor-pointer hover:bg-gray-50"
                    onClick={() => navigate(`/companies/${record.code}`)}
                  >
                    <td className="border-b border-gray-200 px-3 py-2 tabular-nums">{index + 1}</td>
                    <td className="border-b border-gray-200 px-3 py-2">{record.name}</td>
                    <td className="border-b border-gray-200 px-3 py-2">{record.code}</td>
                    <td className="border-b border-gray-200 px-3 py-2">{record.sector ?? "業種不明"}</td>
                    <td className="border-b border-gray-200 px-3 py-2 text-right tabular-nums">
                      {formatValue(record.value, metricOption.kind)}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )
      )}
    </div>
  );
}
