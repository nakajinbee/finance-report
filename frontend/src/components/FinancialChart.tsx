import { Bar, BarChart, CartesianGrid, Legend, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import type { FinancialRecord } from "../api/client";
import { formatYenForDisplay, yenToOku } from "../lib/formatCurrency";
import { METRIC_DEFINITIONS, getMetricValue, type MetricKey } from "../lib/metrics";

type FinancialChartProps = {
  records: FinancialRecord[];
  activeMetrics: Set<MetricKey>;
};

type ChartDatum = { fiscal_year: string } & Partial<Record<MetricKey, number | null>>;

function toChartData(records: FinancialRecord[]): ChartDatum[] {
  return records.map((record) => {
    const datum: ChartDatum = { fiscal_year: record.fiscal_year };
    for (const metric of METRIC_DEFINITIONS) {
      const yen = getMetricValue(record, metric.key);
      datum[metric.key] = yen === null ? null : yenToOku(yen);
    }
    return datum;
  });
}

function ChartTooltip({
  active,
  label,
  records,
  activeMetrics,
}: {
  active?: boolean;
  label?: string;
  records: FinancialRecord[];
  activeMetrics: Set<MetricKey>;
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
      {METRIC_DEFINITIONS.filter((metric) => activeMetrics.has(metric.key)).map((metric) => (
        <p key={metric.key} style={{ color: metric.color }}>
          {metric.label}：{formatYenForDisplay(getMetricValue(record, metric.key))}
        </p>
      ))}
    </div>
  );
}

export function FinancialChart({ records, activeMetrics }: FinancialChartProps) {
  const chartData = toChartData(records);
  const activeMetricDefinitions = METRIC_DEFINITIONS.filter((metric) => activeMetrics.has(metric.key));

  return (
    <ResponsiveContainer width="100%" height={400}>
      <BarChart data={chartData}>
        <CartesianGrid strokeDasharray="3 3" />
        <XAxis dataKey="fiscal_year" />
        <YAxis unit="億円" />
        <Tooltip content={<ChartTooltip records={records} activeMetrics={activeMetrics} />} />
        <Legend />
        {activeMetricDefinitions.map((metric) => (
          <Bar key={metric.key} dataKey={metric.key} name={metric.label} fill={metric.color} />
        ))}
      </BarChart>
    </ResponsiveContainer>
  );
}
