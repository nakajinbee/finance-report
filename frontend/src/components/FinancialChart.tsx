import { Bar, BarChart, CartesianGrid, Legend, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import type { FinancialRecord } from "../api/client";
import { formatYenForDisplay, yenToOku } from "../lib/formatCurrency";
import { toFiscalYearAxisLabel } from "../lib/formatFiscalYear";
import { getMetricValue, type MetricDefinition, type MetricKey } from "../lib/metrics";

type FinancialChartProps = {
  records: FinancialRecord[];
  definitions: MetricDefinition[];
  activeMetrics: Set<MetricKey>;
};

type ChartDatum = { fiscal_year: string } & Partial<Record<MetricKey, number | null>>;

function toChartData(records: FinancialRecord[], definitions: MetricDefinition[]): ChartDatum[] {
  return records.map((record) => {
    const datum: ChartDatum = { fiscal_year: record.fiscal_year };
    for (const metric of definitions) {
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
  definitions,
  activeMetrics,
}: {
  active?: boolean;
  label?: string;
  records: FinancialRecord[];
  definitions: MetricDefinition[];
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
      {definitions
        .filter((metric) => activeMetrics.has(metric.key))
        .map((metric) => (
          <p key={metric.key} style={{ color: metric.color }}>
            {metric.label}：{formatYenForDisplay(getMetricValue(record, metric.key))}
          </p>
        ))}
    </div>
  );
}

export function FinancialChart({ records, definitions, activeMetrics }: FinancialChartProps) {
  const chartData = toChartData(records, definitions);
  const activeMetricDefinitions = definitions.filter((metric) => activeMetrics.has(metric.key));

  return (
    <ResponsiveContainer width="100%" height={320}>
      <BarChart data={chartData} margin={{ left: 8 }}>
        <CartesianGrid strokeDasharray="3 3" />
        <XAxis dataKey="fiscal_year" tickFormatter={toFiscalYearAxisLabel} />
        <YAxis unit="億円" width={80} />
        <Tooltip content={<ChartTooltip records={records} definitions={definitions} activeMetrics={activeMetrics} />} />
        <Legend />
        {activeMetricDefinitions.map((metric) => (
          <Bar key={metric.key} dataKey={metric.key} name={metric.label} fill={metric.color} />
        ))}
      </BarChart>
    </ResponsiveContainer>
  );
}
