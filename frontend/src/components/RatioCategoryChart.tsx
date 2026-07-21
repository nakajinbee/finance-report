import { Bar, BarChart, CartesianGrid, Legend, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import type { RatioRecord } from "../api/client";
import { formatByRatioFormat } from "../lib/formatRatio";
import { getRatioValue, toChartValue, type RatioKey, type RatioMetricDefinition } from "../lib/ratioCategories";

type RatioCategoryChartProps = {
  records: RatioRecord[];
  definitions: RatioMetricDefinition[];
  activeKeys: Set<RatioKey>;
};

type ChartDatum = { fiscal_year: string } & Partial<Record<RatioKey, number | null>>;

function toChartData(records: RatioRecord[], definitions: RatioMetricDefinition[]): ChartDatum[] {
  return records.map((record) => {
    const datum: ChartDatum = { fiscal_year: record.fiscal_year };
    for (const metric of definitions) {
      datum[metric.key] = toChartValue(getRatioValue(record, metric.key), metric.format);
    }
    return datum;
  });
}

function ChartTooltip({
  active,
  label,
  records,
  definitions,
  activeKeys,
}: {
  active?: boolean;
  label?: string;
  records: RatioRecord[];
  definitions: RatioMetricDefinition[];
  activeKeys: Set<RatioKey>;
}) {
  if (!active) {
    return null;
  }
  const record = records.find((r) => r.fiscal_year === label);
  if (!record) {
    return null;
  }
  return (
    <div className="rounded border border-gray-200 bg-white px-3 py-2 shadow">
      <p className="mb-1 font-medium">{label}</p>
      {definitions
        .filter((metric) => activeKeys.has(metric.key))
        .map((metric) => (
          <p key={metric.key} style={{ color: metric.color }}>
            {metric.label}：{formatByRatioFormat(getRatioValue(record, metric.key), metric.format)}
          </p>
        ))}
    </div>
  );
}

export function RatioCategoryChart({ records, definitions, activeKeys }: RatioCategoryChartProps) {
  const chartData = toChartData(records, definitions);
  const activeDefinitions = definitions.filter((metric) => activeKeys.has(metric.key));
  const hasDualAxis = definitions.some((metric) => metric.axis === "right");

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
        <Tooltip content={<ChartTooltip records={records} definitions={definitions} activeKeys={activeKeys} />} />
        <Legend />
        {activeDefinitions.map((metric) => (
          <Bar
            key={metric.key}
            dataKey={metric.key}
            name={metric.label}
            fill={metric.color}
            yAxisId={hasDualAxis ? (metric.axis ?? "left") : undefined}
          />
        ))}
      </BarChart>
    </ResponsiveContainer>
  );
}
