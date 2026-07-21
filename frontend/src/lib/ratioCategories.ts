import type { RatioRecord } from "../api/client";

export type RatioKey = Exclude<keyof RatioRecord, "fiscal_year" | "period_end">;

export type RatioFormat = "percent" | "turnover" | "number";

export type RatioMetricDefinition = {
  key: RatioKey;
  label: string;
  color: string;
  format: RatioFormat;
  /** 投資指標カテゴリのみ、単位が異なる系列を2軸に振り分けるために使う */
  axis?: "left" | "right";
};

// FR-28：既存12指標を4カテゴリに分類する
export const PROFITABILITY_RATIOS: RatioMetricDefinition[] = [
  { key: "roe", label: "ROE（自己資本利益率）", color: "#4E79A7", format: "percent" },
  { key: "roa", label: "ROA（総資産利益率）", color: "#F28E2B", format: "percent" },
  { key: "operating_margin", label: "売上高営業利益率", color: "#59A14F", format: "percent" },
  { key: "net_margin", label: "売上高純利益率", color: "#B07AA1", format: "percent" },
];

export const EFFICIENCY_RATIOS: RatioMetricDefinition[] = [
  { key: "total_asset_turnover", label: "総資産回転率", color: "#4E79A7", format: "turnover" },
  { key: "inventory_turnover", label: "棚卸資産回転率", color: "#F28E2B", format: "turnover" },
];

export const SAFETY_RATIOS: RatioMetricDefinition[] = [
  { key: "current_ratio", label: "流動比率", color: "#4E79A7", format: "percent" },
  { key: "fixed_ratio", label: "固定比率", color: "#F28E2B", format: "percent" },
  { key: "equity_ratio", label: "自己資本比率", color: "#59A14F", format: "percent" },
];

// 単位が円・倍・%と異なるため、チャートは2軸（EPS=左軸、PER・配当性向=右軸）にする
export const INVESTMENT_RATIOS: RatioMetricDefinition[] = [
  { key: "eps", label: "EPS（1株当たり当期純利益）", color: "#4E79A7", format: "number", axis: "left" },
  { key: "per", label: "PER（株価収益率）", color: "#F28E2B", format: "number", axis: "right" },
  { key: "payout_ratio", label: "配当性向", color: "#59A14F", format: "percent", axis: "right" },
];

export function getRatioValue(record: RatioRecord, key: RatioKey): number | null {
  return record[key];
}

/** チャート描画用に、%指標は0-100スケールの数値に変換する（表示はformatRatio側で行う） */
export function toChartValue(value: number | null, format: RatioFormat): number | null {
  if (value === null) {
    return null;
  }
  return format === "percent" ? value * 100 : value;
}
