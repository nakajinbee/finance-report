# サイクル4 設計書

対象：[cycle4_requirements.md](../requirements/cycle4_requirements.md) FR-29〜32

---

## 1. FR-32：仮の配色・スタイル（他のFRの前提のため最初に設計する）

### `frontend/src/lib/theme.ts`（新規）

```typescript
/**
 * サイクル4の仮の配色定義。
 * 本格的なデザインコンセプト・配色は「サイクル5・6」で決定する。
 * ここでの値は暫定であり、サイクル5・6で置き換わることを前提とする。
 */
export const THEME = {
  background: "#ffffff",
  surface: "#f9fafb",   // Tailwind gray-50相当
  border: "#e5e7eb",    // Tailwind gray-200相当
  textPrimary: "#111827",  // Tailwind gray-900相当
  textSecondary: "#6b7280", // Tailwind gray-500相当
  accent: "#2563eb",    // Tailwind blue-600相当（既存のボタン色を踏襲）
};

// グラフの系列色（Tableau10ベース、既存の複数コンポーネントに散在していたものを集約）
export const CHART_COLORS = {
  series1: "#4E79A7",
  series2: "#F28E2B",
  series3: "#59A14F",
  series4: "#B07AA1",
  series5: "#E15759",
  series6: "#76B7B2",
  series7: "#EDC948",
} as const;

// 指標の「内訳（生の金額）」用の色（指標本体の色と別系統にして見分けやすくする）
export const COMPONENT_CHART_COLORS = ["#BAB0AC", "#D37295", "#8CD17D", "#FABFD2", "#9D7660"] as const;
```

`lib/metrics.ts`・`lib/ratioCategories.ts`・`components/CashFlowChart.tsx`にハードコートされている
色コード（`#4E79A7`等）を、`CHART_COLORS.series1`等の参照に置き換える。
色の実際の値そのものは変更しない（既存の見た目を壊さない、リファクタリングに徹する）。

Tailwindの`@theme`ディレクティブは、ヘッダー・フッター等の**UI装飾色**（背景・文字色・
アクセント）にのみ使う。グラフの系列色はRechartsに直接渡す値のため、TypeScriptの定数
（`CHART_COLORS`）で管理する（TailwindのCSS変数をJS側から読むのは煩雑なため）。

`frontend/src/index.css`に以下を追加：
```css
@import "tailwindcss";

@theme {
  --color-brand: #2563eb;
  --color-brand-dark: #1d4ed8;
}
```

---

## 2. FR-29〜30：共通ヘッダー・フッター

### コンポーネント構成

```
frontend/src/components/layout/
  Header.tsx   — アプリ名＋「企業一覧」リンク
  Footer.tsx   — データ出典表示
  Layout.tsx   — Header + <Outlet /> + Footer
```

### `Layout.tsx`
```tsx
import { Outlet } from "react-router-dom";
import { Header } from "./Header";
import { Footer } from "./Footer";

export function Layout() {
  return (
    <div className="flex min-h-screen flex-col">
      <Header />
      <main className="flex-1">
        <Outlet />
      </main>
      <Footer />
    </div>
  );
}
```

### `App.tsx`の変更
現状はトップレベルで各ページを`<Route path=... element=.../>`しているが、
`Layout`を親ルートにしたネスト構造に変更する（React Router v7の`<Outlet/>`パターン）：

```tsx
<Routes>
  <Route element={<Layout />}>
    <Route path="/" element={<AppEntry />} />
    <Route path="/download" element={<DownloadPage />} />
    <Route path="/companies" element={<CompanyListPage />} />
    <Route path="/companies/:code" element={<CompanyDetailPage />} />
    <Route path="/companies/:code/facts" element={<CompanyFactsPage />} />
  </Route>
</Routes>
```

各ページ内の`max-w-3xl`等のコンテナ幅指定は既存のまま維持する（`Layout`の`<main>`は
幅を制約しない。ページごとの最大幅はこれまで通り各ページコンポーネントの責務とする）。

### Header内容
- アプリ名（仮称「企業会計情報」）をクリックで`/`へ、または明示的に`/companies`へのリンクを
  併設する（FR-29のとおり「企業一覧への導線」として、テキストリンク`企業一覧`を右側に配置）

### Footer内容
- 中央または左寄せで「データ出典：EDINET（金融庁）」の1行のみ

---

## 3. FR-31：グラフの見やすさ改善

- 前述の通り色コードを`CHART_COLORS`に集約する（配色の値自体は変更しない）
- `CompanyDetailPage.tsx`内の各セクション（B/S・P/L・CF・財務分析指標）の見出しレベルを
  `<h2>`に統一する（現状、財務分析指標配下のカテゴリ見出し`<h3>`はそのまま維持し、
  カテゴリ内の粒度であることを示す）。セクション間の余白（`space-y-*`）も統一する
- 既存の`ResponsiveContainer`・`Tooltip`・`Legend`の実装は変更しない
  （軸ラベル・単位表示はサイクル3で既に対応済みのため、本サイクルでは追加作業なし）

---

## 検証方法

1. `tsc -b --noEmit`・`oxlint`が通ることを確認
2. 開発サーバー（vite HMR）で全画面（SCR-001〜004）を表示し、ヘッダー・フッターが
   共通して表示されること、既存の機能（検索・ダウンロード・グラフ表示・トグル）が
   壊れていないことを確認
3. グラフの配色が変更前と同じであること（値のリファクタリングのみで見た目は変えない）を
   目視確認
