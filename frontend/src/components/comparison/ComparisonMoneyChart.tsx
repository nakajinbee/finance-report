import { Bar, BarChart, CartesianGrid, Legend, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { formatYenForDisplay, yenToOku } from "../../lib/formatCurrency";

export type ComparisonMoneyDatum = { code: string; name: string; [key: string]: number | string | null };

export type ComparisonMoneyMetric = { key: string; label: string; color: string };

type ComparisonMoneyChartProps = {
  data: ComparisonMoneyDatum[];
  metrics: ComparisonMoneyMetric[];
};

type ChartDatum = { name: string; code: string; [key: string]: number | string | null };

function toChartData(data: ComparisonMoneyDatum[], metrics: ComparisonMoneyMetric[]): ChartDatum[] {
  return data.map((datum) => {
    const chartDatum: ChartDatum = { name: datum.name, code: datum.code };
    for (const metric of metrics) {
      const yen = (datum[metric.key] ?? null) as number | null;
      chartDatum[metric.key] = yen === null ? null : yenToOku(yen);
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
  data: ComparisonMoneyDatum[];
  metrics: ComparisonMoneyMetric[];
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
          {metric.label}：{formatYenForDisplay((datum[metric.key] ?? null) as number | null)}
        </p>
      ))}
    </div>
  );
}

export function ComparisonMoneyChart({ data, metrics }: ComparisonMoneyChartProps) {
  const chartData = toChartData(data, metrics);

  return (
    <ResponsiveContainer width="100%" height={320}>
      <BarChart data={chartData} margin={{ left: 8 }}>
        <CartesianGrid strokeDasharray="3 3" stroke="#E5E7EB" />
        <XAxis dataKey="name" />
        <YAxis unit="億円" width={80} />
        <Tooltip content={<ChartTooltip data={data} metrics={metrics} />} />
        <Legend itemSorter={null} />
        {metrics.map((metric) => (
          <Bar key={metric.key} dataKey={metric.key} name={metric.label} fill={metric.color} />
        ))}
      </BarChart>
    </ResponsiveContainer>
  );
}
