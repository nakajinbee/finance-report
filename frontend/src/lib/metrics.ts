import type { FinancialRecord } from "../api/client";

export type MetricKey =
  | "revenue"
  | "operating_profit"
  | "ordinary_profit"
  | "net_profit"
  | "total_assets"
  | "total_liabilities"
  | "equity";

export type MetricDefinition = {
  key: MetricKey;
  label: string;
  color: string;
};

// SCR-003_company_detail.md「指標のカラーリング」のとおり。P/L（損益計算書）系列
export const PL_METRIC_DEFINITIONS: MetricDefinition[] = [
  { key: "revenue", label: "売上高", color: "#4E79A7" },
  { key: "operating_profit", label: "営業利益", color: "#F28E2B" },
  // 経常利益はJapan GAAP特有の概念のため、IFRS/US GAAP企業では常にデータなしになる
  { key: "ordinary_profit", label: "経常利益", color: "#EDC948" },
  { key: "net_profit", label: "純利益", color: "#59A14F" },
];

// B/S（貸借対照表）系列
export const BS_METRIC_DEFINITIONS: MetricDefinition[] = [
  { key: "total_assets", label: "総資産", color: "#B07AA1" },
  { key: "total_liabilities", label: "負債", color: "#E15759" },
  { key: "equity", label: "自己資本（純資産）", color: "#76B7B2" },
];

export function getMetricValue(record: FinancialRecord, key: MetricKey): number | null {
  return record[key];
}
