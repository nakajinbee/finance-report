/** ひらがなをカタカナに変換する（SCR-002の検索バー：ひらがな・カタカナを区別しない要件用） */
function hiraganaToKatakana(text: string): string {
  return text.replace(/[ぁ-ゖ]/g, (char) => String.fromCharCode(char.charCodeAt(0) + 0x60));
}

/** 検索用に大文字小文字・ひらがな/カタカナの差異を吸収した正規化文字列を返す */
export function normalizeForSearch(text: string): string {
  return hiraganaToKatakana(text).toLowerCase();
}
