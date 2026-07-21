import type { ButtonHTMLAttributes } from "react";

type ButtonProps = {
  variant?: "primary" | "secondary";
} & ButtonHTMLAttributes<HTMLButtonElement>;

/** サイクル4 FR-33：画面ごとにバラバラだったボタンのスタイルを統一する共通コンポーネント */
export function Button({
  variant = "primary",
  className,
  children,
  ...props
}: ButtonProps) {
  const base =
    "rounded px-4 py-2 text-sm font-medium transition-colors disabled:cursor-not-allowed disabled:opacity-50";
  const style =
    variant === "primary"
      ? "bg-brand text-white hover:bg-brand-dark"
      : "border border-gray-300 text-gray-700 hover:bg-gray-50";
  return (
    <button className={`${base} ${style} ${className ?? ""}`} {...props}>
      {children}
    </button>
  );
}
