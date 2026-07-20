import type { FinancialRecord } from "../api/client";

export type MetricKey = "revenue" | "operating_profit" | "net_profit" | "total_assets" | "total_liabilities";

export type MetricDefinition = {
  key: MetricKey;
  label: string;
  color: string;
};

// SCR-003_company_detail.md「指標のカラーリング」のとおり
export const METRIC_DEFINITIONS: MetricDefinition[] = [
  { key: "revenue", label: "売上高", color: "#4E79A7" },
  { key: "operating_profit", label: "営業利益", color: "#F28E2B" },
  { key: "net_profit", label: "純利益", color: "#59A14F" },
  { key: "total_assets", label: "総資産", color: "#B07AA1" },
  { key: "total_liabilities", label: "負債合計", color: "#E15759" },
];

export function getMetricValue(record: FinancialRecord, key: MetricKey): number | null {
  return record[key];
}
