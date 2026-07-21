/** 比率（ROE・自己資本比率等）を「XX.X%」表示に変換する（SCR-003 財務分析指標セクション） */
export function formatPercentForDisplay(value: number | null): string {
  if (value === null) {
    return "データなし";
  }
  return `${(value * 100).toFixed(1)}%`;
}

/** 回転率（総資産回転率・棚卸資産回転率）を「X.X回」表示に変換する */
export function formatTurnoverForDisplay(value: number | null): string {
  if (value === null) {
    return "データなし";
  }
  return `${value.toFixed(1)}回`;
}

/** EPS・PERなど、単位のない数値を小数第2位までの表示に変換する */
export function formatNumberForDisplay(value: number | null): string {
  if (value === null) {
    return "データなし";
  }
  return value.toFixed(2);
}

/** RatioFormat（"percent"|"turnover"|"number"）に応じたフォーマット関数へ振り分ける */
export function formatByRatioFormat(value: number | null, format: "percent" | "turnover" | "number"): string {
  if (format === "percent") {
    return formatPercentForDisplay(value);
  }
  if (format === "turnover") {
    return formatTurnoverForDisplay(value);
  }
  return formatNumberForDisplay(value);
}
