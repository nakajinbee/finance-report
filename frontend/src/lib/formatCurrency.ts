const YEN_PER_OKU = 100_000_000;
const OKU_PER_CHO = 10_000;

/** 円をグラフ縦軸用の億円単位に変換する（SCR-003：単位は億円） */
export function yenToOku(yen: number): number {
  return yen / YEN_PER_OKU;
}

/** 円を「X.X兆円」（1兆円以上）または「X,XXX億円」（1兆円未満）の表示文字列に変換する
 * （SCR-003-13 ツールチップの金額表示形式） */
export function formatYenForDisplay(yen: number | null): string {
  if (yen === null) {
    return "データなし";
  }
  const oku = yenToOku(yen);
  if (oku >= OKU_PER_CHO) {
    return `${(oku / OKU_PER_CHO).toFixed(1)}兆円`;
  }
  return `${Math.round(oku).toLocaleString()}億円`;
}
