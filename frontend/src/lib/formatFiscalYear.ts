/**
 * 表示用会計年度文字列（例："2021年3月期"）から、グラフの軸ラベル用に年だけを取り出す。
 * fiscal_year自体（date_format_policy.md準拠、period_endから動的生成しない文字列）は
 * ツールチップ・表ではそのまま使い続け、ここでは軸のラベル表示のみを簡略化する
 * （ユーザー要望、2026-07-22：「2021年3月期」ではなく「2021」だけでよい）。
 */
export function toFiscalYearAxisLabel(fiscalYear: string): string {
  const match = fiscalYear.match(/^(\d+)年/);
  return match ? match[1] : fiscalYear;
}
