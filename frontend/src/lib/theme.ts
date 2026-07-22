// グラフの系列色（Tableau10ベース）。複数のグラフコンポーネントに散在していた色コードを集約した
export const CHART_COLORS = {
  series1: "#4E79A7",
  series2: "#F28E2B",
  series3: "#59A14F",
  series4: "#B07AA1",
  series5: "#E15759",
  series6: "#76B7B2",
  series7: "#EDC948",
} as const;

// 指標の「内訳（生の金額）」用の色（指標本体の色とは別系統にして見分けやすくする）
export const COMPONENT_CHART_COLORS = [
  "#BAB0AC",
  "#D37295",
  "#8CD17D",
  "#FABFD2",
  "#9D7660",
] as const;

// キャッシュフロー計算書グラフ専用の色（既存の見た目を変えないよう、CHART_COLORSとは別に集約）
export const CASH_FLOW_CHART_COLORS = {
  operating: "#1F3864",
  investing: "#6699CC",
  financing: "#F28E2B",
} as const;
