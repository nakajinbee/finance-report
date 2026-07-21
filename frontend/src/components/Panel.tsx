import type { ReactNode } from "react";

type PanelProps = {
  children: ReactNode;
  className?: string;
};

/** サイクル4 FR-33：セクション・一覧行を区切る共通のカード表現 */
export function Panel({ children, className }: PanelProps) {
  return (
    <div
      className={`rounded-lg border border-gray-200 bg-white p-6 shadow-sm ${className ?? ""}`}
    >
      {children}
    </div>
  );
}
