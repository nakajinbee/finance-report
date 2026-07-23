import { useState } from "react";

type QualitativeFactSectionProps = {
  title: string;
  content: string | null;
};

// EDINETのCSVは句点で文が続くだけで改行を含まないため、句点ごとに改行して読みやすくする
// （表由来の箇所は区切り文字自体が失われておりこの変換でも直らない。既知の制約）
function splitIntoSentences(content: string): string[] {
  return content
    .split("。")
    .map((sentence) => sentence.trim())
    .filter((sentence) => sentence.length > 0)
    .map((sentence) => `${sentence}。`);
}

/** SCR-003 事業概要・リスクセクションの1項目（開閉式）を表示する共通コンポーネント（サイクル13 FR-58） */
export function QualitativeFactSection({ title, content }: QualitativeFactSectionProps) {
  const [isOpen, setIsOpen] = useState(false);

  if (content === null) {
    return null;
  }

  const sentences = splitIntoSentences(content);

  return (
    <div className="border-b border-gray-200 last:border-b-0">
      <button
        type="button"
        onClick={() => setIsOpen((current) => !current)}
        className="flex w-full items-center justify-between py-3 text-left font-medium text-gray-900"
      >
        <span>{title}</span>
        <span className="text-gray-400">{isOpen ? "▾" : "▸"}</span>
      </button>
      {isOpen && (
        <div className="space-y-2 pb-4 text-sm text-gray-700">
          {sentences.map((sentence, i) => (
            <p key={i}>{sentence}</p>
          ))}
        </div>
      )}
    </div>
  );
}
