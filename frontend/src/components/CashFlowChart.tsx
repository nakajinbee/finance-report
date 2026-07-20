import { Bar, BarChart, CartesianGrid, Legend, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import type { CashFlowRecord } from "../api/client";
import { formatYenForDisplay, yenToOku } from "../lib/formatCurrency";

type CashFlowChartProps = {
  records: CashFlowRecord[];
};

type CashFlowKey = "operating_cash_flow" | "investing_cash_flow" | "financing_cash_flow";

const CF_DEFINITIONS: { key: CashFlowKey; label: string; color: string }[] = [
  { key: "operating_cash_flow", label: "営業CF", color: "#1F3864" },
  { key: "investing_cash_flow", label: "投資CF", color: "#6699CC" },
  { key: "financing_cash_flow", label: "財務CF", color: "#F28E2B" },
];

type ChartDatum = { fiscal_year: string } & Partial<Record<CashFlowKey, number | null>>;

function toChartData(records: CashFlowRecord[]): ChartDatum[] {
  return records.map((record) => {
    const datum: ChartDatum = { fiscal_year: record.fiscal_year };
    for (const cf of CF_DEFINITIONS) {
      const yen = record[cf.key];
      datum[cf.key] = yen === null ? null : yenToOku(yen);
    }
    return datum;
  });
}

function ChartTooltip({
  active,
  label,
  records,
}: {
  active?: boolean;
  label?: string;
  records: CashFlowRecord[];
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
      {CF_DEFINITIONS.map((cf) => (
        <p key={cf.key} style={{ color: cf.color }}>
          {cf.label}：{formatYenForDisplay(record[cf.key])}
        </p>
      ))}
    </div>
  );
}

export function CashFlowChart({ records }: CashFlowChartProps) {
  const chartData = toChartData(records);

  return (
    <ResponsiveContainer width="100%" height={320}>
      <BarChart data={chartData}>
        <CartesianGrid strokeDasharray="3 3" />
        <XAxis dataKey="fiscal_year" />
        <YAxis unit="億円" />
        <Tooltip content={<ChartTooltip records={records} />} />
        <Legend />
        {CF_DEFINITIONS.map((cf) => (
          <Bar key={cf.key} dataKey={cf.key} name={cf.label} fill={cf.color} />
        ))}
      </BarChart>
    </ResponsiveContainer>
  );
}
