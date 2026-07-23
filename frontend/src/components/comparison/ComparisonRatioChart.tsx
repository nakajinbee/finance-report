import { Bar, BarChart, CartesianGrid, Legend, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { formatByRatioFormat } from "../../lib/formatRatio";
import type { RatioFormat } from "../../lib/ratioCategories";

export type ComparisonRatioDatum = { code: string; name: string; [key: string]: number | string | null };

export type ComparisonRatioMetric = { key: string; label: string; color: string; format: RatioFormat };

type ComparisonRatioChartProps = {
  data: ComparisonRatioDatum[];
  metrics: ComparisonRatioMetric[];
};

type ChartDatum = { name: string; code: string; [key: string]: number | string | null };

function toChartData(data: ComparisonRatioDatum[], metrics: ComparisonRatioMetric[]): ChartDatum[] {
  return data.map((datum) => {
    const chartDatum: ChartDatum = { name: datum.name, code: datum.code };
    for (const metric of metrics) {
      chartDatum[metric.key] = (datum[metric.key] ?? null) as number | null;
    }
    return chartDatum;
  });
}

function ChartTooltip({
  active,
  label,
  data,
  metrics,
}: {
  active?: boolean;
  label?: string;
  data: ComparisonRatioDatum[];
  metrics: ComparisonRatioMetric[];
}) {
  if (!active) {
    return null;
  }
  const datum = data.find((d) => d.name === label);
  if (!datum) {
    return null;
  }
  return (
    <div className="rounded border border-gray-200 bg-white px-3 py-2 shadow">
      <p className="mb-1 font-medium">{label}</p>
      {metrics.map((metric) => (
        <p key={metric.key} style={{ color: metric.color }}>
          {metric.label}：{formatByRatioFormat((datum[metric.key] ?? null) as number | null, metric.format)}
        </p>
      ))}
    </div>
  );
}

export function ComparisonRatioChart({ data, metrics }: ComparisonRatioChartProps) {
  const chartData = toChartData(data, metrics);

  return (
    <ResponsiveContainer width="100%" height={320}>
      <BarChart data={chartData} margin={{ left: 8 }}>
        <CartesianGrid strokeDasharray="3 3" stroke="#E5E7EB" />
        <XAxis dataKey="name" />
        <YAxis width={60} />
        <Tooltip content={<ChartTooltip data={data} metrics={metrics} />} />
        <Legend itemSorter={null} />
        {metrics.map((metric) => (
          <Bar key={metric.key} dataKey={metric.key} name={metric.label} fill={metric.color} />
        ))}
      </BarChart>
    </ResponsiveContainer>
  );
}
