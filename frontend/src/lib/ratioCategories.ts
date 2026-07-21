import type { FinancialRecord, RatioRecord } from "../api/client";
import { formatYenForDisplay, yenToOku } from "./formatCurrency";
import { formatByRatioFormat } from "./formatRatio";

export type RatioKey = Exclude<keyof RatioRecord, "fiscal_year" | "period_end">;

export type RatioFormat = "percent" | "turnover" | "number";

type FinancialComponentKey = "revenue" | "operating_profit" | "net_profit" | "total_assets" | "equity";
type RatioComponentKey =
  | "current_assets"
  | "current_liabilities"
  | "non_current_assets"
  | "non_current_liabilities"
  | "inventories";

// 指標計算の元になった生の金額（ユーザー要望、2026-07-22）。B/S・P/Lの主要項目は
// FinancialRecordから、安全性・効率性特有の内訳項目はRatioRecordから参照する
export type ComponentDefinition =
  | { key: FinancialComponentKey; label: string; source: "financial" }
  | { key: RatioComponentKey; label: string; source: "ratio" };

export function getComponentValue(
  financial: FinancialRecord | undefined,
  ratio: RatioRecord | undefined,
  component: ComponentDefinition,
): number | null {
  if (component.source === "financial") {
    return financial ? financial[component.key] : null;
  }
  return ratio ? ratio[component.key] : null;
}

export type RatioMetricDefinition = {
  key: RatioKey;
  label: string;
  color: string;
  format: RatioFormat;
  /** グラフの軸ラベルに表示する単位（%・回・円・倍など） */
  unit: string;
  /** 投資指標カテゴリのみ、単位が異なる系列を2軸に振り分けるために使う */
  axis?: "left" | "right";
  /** この指標の計算に使った生の金額（表にのみ表示、グラフには出さない） */
  components?: ComponentDefinition[];
};

// FR-28：既存12指標を4カテゴリに分類する
export const PROFITABILITY_RATIOS: RatioMetricDefinition[] = [
  {
    key: "roe",
    label: "ROE（自己資本利益率）",
    color: "#4E79A7",
    format: "percent",
    unit: "%",
    components: [
      { key: "net_profit", label: "純利益", source: "financial" },
      { key: "equity", label: "自己資本（純資産）", source: "financial" },
    ],
  },
  {
    key: "roa",
    label: "ROA（総資産利益率）",
    color: "#F28E2B",
    format: "percent",
    unit: "%",
    components: [
      { key: "net_profit", label: "純利益", source: "financial" },
      { key: "total_assets", label: "総資産", source: "financial" },
    ],
  },
  {
    key: "operating_margin",
    label: "売上高営業利益率",
    color: "#59A14F",
    format: "percent",
    unit: "%",
    components: [
      { key: "operating_profit", label: "営業利益", source: "financial" },
      { key: "revenue", label: "売上高", source: "financial" },
    ],
  },
  {
    key: "net_margin",
    label: "売上高純利益率",
    color: "#B07AA1",
    format: "percent",
    unit: "%",
    components: [
      { key: "net_profit", label: "純利益", source: "financial" },
      { key: "revenue", label: "売上高", source: "financial" },
    ],
  },
];

export const EFFICIENCY_RATIOS: RatioMetricDefinition[] = [
  {
    key: "total_asset_turnover",
    label: "総資産回転率",
    color: "#4E79A7",
    format: "turnover",
    unit: "回",
    components: [
      { key: "revenue", label: "売上高", source: "financial" },
      { key: "total_assets", label: "総資産", source: "financial" },
    ],
  },
  {
    key: "inventory_turnover",
    label: "棚卸資産回転率",
    color: "#F28E2B",
    format: "turnover",
    unit: "回",
    components: [
      { key: "revenue", label: "売上高", source: "financial" },
      { key: "inventories", label: "棚卸資産", source: "ratio" },
    ],
  },
];

export const SAFETY_RATIOS: RatioMetricDefinition[] = [
  {
    key: "current_ratio",
    label: "流動比率",
    color: "#4E79A7",
    format: "percent",
    unit: "%",
    components: [
      { key: "current_assets", label: "流動資産", source: "ratio" },
      { key: "current_liabilities", label: "流動負債", source: "ratio" },
    ],
  },
  {
    key: "fixed_ratio",
    label: "固定比率",
    color: "#F28E2B",
    format: "percent",
    unit: "%",
    components: [
      { key: "non_current_assets", label: "固定資産", source: "ratio" },
      { key: "non_current_liabilities", label: "固定負債", source: "ratio" },
      { key: "equity", label: "自己資本（純資産）", source: "financial" },
    ],
  },
  {
    key: "equity_ratio",
    label: "自己資本比率",
    color: "#59A14F",
    format: "percent",
    unit: "%",
    components: [
      { key: "equity", label: "自己資本（純資産）", source: "financial" },
      { key: "total_assets", label: "総資産", source: "financial" },
    ],
  },
];

// 単位が円・倍・%と異なるため、チャートは2軸（EPS=左軸、PER・配当性向=右軸）にする
export const INVESTMENT_RATIOS: RatioMetricDefinition[] = [
  { key: "eps", label: "EPS（1株当たり当期純利益）", color: "#4E79A7", format: "number", unit: "円", axis: "left" },
  { key: "per", label: "PER（株価収益率）", color: "#F28E2B", format: "number", unit: "倍", axis: "right" },
  { key: "payout_ratio", label: "配当性向", color: "#59A14F", format: "percent", unit: "%", axis: "right" },
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

// グラフに指標本体と内訳（生の金額）の両方を表示するための統一エントリ（ユーザー要望、2026-07-22）。
// 指標本体は%・回・円・倍軸（既存のaxis指定）、内訳（生の金額）は億円軸に統一して2軸目に表示する
export type CategoryChartEntry = {
  key: string;
  label: string;
  color: string;
  axis: "left" | "right";
  isComponent: boolean;
  getChartValue: (financial: FinancialRecord | undefined, ratio: RatioRecord | undefined) => number | null;
  getDisplayValue: (financial: FinancialRecord | undefined, ratio: RatioRecord | undefined) => string;
};

// 内訳（生の金額）系列の色。指標本体の色（Tableau10系）とは別系統にして見分けやすくする
const COMPONENT_COLORS = ["#BAB0AC", "#D37295", "#8CD17D", "#FABFD2", "#9D7660"];

export function buildCategoryChartEntries(definitions: RatioMetricDefinition[]): CategoryChartEntry[] {
  const ratioEntries: CategoryChartEntry[] = definitions.map((metric) => ({
    key: metric.key,
    label: metric.label,
    color: metric.color,
    axis: metric.axis ?? "left",
    isComponent: false,
    getChartValue: (_financial, ratio) => (ratio ? toChartValue(getRatioValue(ratio, metric.key), metric.format) : null),
    getDisplayValue: (_financial, ratio) => formatByRatioFormat(ratio ? getRatioValue(ratio, metric.key) : null, metric.format),
  }));

  const seenComponentKeys = new Set<string>();
  const componentEntries: CategoryChartEntry[] = [];
  for (const metric of definitions) {
    for (const component of metric.components ?? []) {
      if (seenComponentKeys.has(component.key)) {
        continue;
      }
      seenComponentKeys.add(component.key);
      componentEntries.push({
        key: component.key,
        label: component.label,
        color: COMPONENT_COLORS[componentEntries.length % COMPONENT_COLORS.length],
        axis: "right",
        isComponent: true,
        getChartValue: (financial, ratio) => {
          const yen = getComponentValue(financial, ratio, component);
          return yen === null ? null : yenToOku(yen);
        },
        getDisplayValue: (financial, ratio) => formatYenForDisplay(getComponentValue(financial, ratio, component)),
      });
    }
  }

  return [...ratioEntries, ...componentEntries];
}
