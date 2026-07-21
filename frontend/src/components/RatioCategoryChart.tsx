import { Bar, BarChart, CartesianGrid, Legend, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import type { FinancialRecord, RatioRecord } from "../api/client";
import type { CategoryChartEntry } from "../lib/ratioCategories";

type RatioCategoryChartProps = {
  financialRecords: FinancialRecord[];
  ratioRecords: RatioRecord[];
  entries: CategoryChartEntry[];
  activeKeys: Set<string>;
};

type ChartDatum = { fiscal_year: string } & Record<string, number | null | string>;

function toChartData(
  financialRecords: FinancialRecord[],
  ratioRecords: RatioRecord[],
  entries: CategoryChartEntry[],
): ChartDatum[] {
  const financialByPeriod = new Map(financialRecords.map((record) => [record.period_end, record]));
  return ratioRecords.map((ratio) => {
    const financial = financialByPeriod.get(ratio.period_end);
    const datum: ChartDatum = { fiscal_year: ratio.fiscal_year };
    for (const entry of entries) {
      datum[entry.key] = entry.getChartValue(financial, ratio);
    }
    return datum;
  });
}

function ChartTooltip({
  active,
  label,
  financialRecords,
  ratioRecords,
  entries,
  activeKeys,
}: {
  active?: boolean;
  label?: string;
  financialRecords: FinancialRecord[];
  ratioRecords: RatioRecord[];
  entries: CategoryChartEntry[];
  activeKeys: Set<string>;
}) {
  if (!active) {
    return null;
  }
  const ratio = ratioRecords.find((r) => r.fiscal_year === label);
  if (!ratio) {
    return null;
  }
  const financial = financialRecords.find((r) => r.period_end === ratio.period_end);
  return (
    <div className="rounded border border-gray-200 bg-white px-3 py-2 shadow">
      <p className="mb-1 font-medium">{label}</p>
      {entries
        .filter((entry) => activeKeys.has(entry.key))
        .map((entry) => (
          <p key={entry.key} style={{ color: entry.color }}>
            {entry.label}：{entry.getDisplayValue(financial, ratio)}
          </p>
        ))}
    </div>
  );
}

export function RatioCategoryChart({ financialRecords, ratioRecords, entries, activeKeys }: RatioCategoryChartProps) {
  const chartData = toChartData(financialRecords, ratioRecords, entries);
  const activeEntries = entries.filter((entry) => activeKeys.has(entry.key));
  const hasDualAxis = entries.some((entry) => entry.axis === "right");

  return (
    <ResponsiveContainer width="100%" height={280}>
      <BarChart data={chartData}>
        <CartesianGrid strokeDasharray="3 3" />
        <XAxis dataKey="fiscal_year" />
        {hasDualAxis ? (
          <>
            <YAxis yAxisId="left" />
            <YAxis yAxisId="right" orientation="right" />
          </>
        ) : (
          <YAxis />
        )}
        <Tooltip
          content={
            <ChartTooltip
              financialRecords={financialRecords}
              ratioRecords={ratioRecords}
              entries={entries}
              activeKeys={activeKeys}
            />
          }
        />
        <Legend />
        {activeEntries.map((entry) => (
          <Bar
            key={entry.key}
            dataKey={entry.key}
            name={entry.label}
            fill={entry.color}
            yAxisId={hasDualAxis ? entry.axis : undefined}
          />
        ))}
      </BarChart>
    </ResponsiveContainer>
  );
}
