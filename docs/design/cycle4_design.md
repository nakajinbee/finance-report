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

## 4. FR-33：仮デザインの「作り込み感」向上

### 4.1 配色（「クールブルー」パレット）

`lib/theme.ts`・`index.css`を以下のように更新する：

```typescript
export const THEME = {
  ...
  accent: "#07575B",      // ocean
  accentDark: "#003B46",  // deep aqua
  accentLight: "#66A5AD", // wave
  tint: "#C4DFE6",        // seafoam
} as const;
```

```css
@theme {
  --color-brand: #07575B;       /* ocean */
  --color-brand-dark: #003B46;  /* deep aqua */
  --color-brand-light: #66A5AD; /* wave */
  --color-tint: #C4DFE6;        /* seafoam */
}
```

`Header`は`bg-brand-dark`（deep aqua、より濃い色でヘッダーらしい重みを出す）、
`Footer`は`bg-tint`（seafoam）、ボタン・トグルの選択状態は`bg-brand`（ocean）に更新する。
`CHART_COLORS`・`COMPONENT_CHART_COLORS`・`CASH_FLOW_CHART_COLORS`は変更しない
（指標の見分けやすさを優先し、Tableau10系の配色のまま維持）。

### 4.2 `Panel`コンポーネント（新規）

```tsx
// frontend/src/components/Panel.tsx
type PanelProps = { children: ReactNode; className?: string };
export function Panel({ children, className }: PanelProps) {
  return (
    <div className={`rounded-lg border border-gray-200 bg-white p-6 shadow-sm ${className ?? ""}`}>
      {children}
    </div>
  );
}
```

`FinancialMetricSection`・キャッシュフロー計算書セクション・`RatioCategorySection`・
`CompanyListPage`の企業カード・`DownloadPage`の検索結果一覧を`Panel`で囲む。
テーブル（`CashFlowTable`・`FinancialMetricTable`・`RatioCategoryTable`・
`CompanyFactsPage`の一覧）のヘッダー行に`bg-gray-50`を追加する。

### 4.3 `Button`コンポーネント（新規）

```tsx
// frontend/src/components/Button.tsx
type ButtonProps = {
  variant?: "primary" | "secondary";
  children: ReactNode;
} & ButtonHTMLAttributes<HTMLButtonElement>;

export function Button({ variant = "primary", className, children, ...props }: ButtonProps) {
  const base = "rounded px-4 py-2 text-sm font-medium disabled:opacity-50";
  const style =
    variant === "primary"
      ? "bg-brand text-white hover:bg-brand-dark disabled:hover:bg-brand"
      : "border border-gray-300 text-gray-700 hover:bg-gray-50";
  return (
    <button className={`${base} ${style} ${className ?? ""}`} {...props}>
      {children}
    </button>
  );
}
```

既存の個別クラス指定ボタン（`DownloadPage`のダウンロード実行、`CompanyDetailPage`の
「企業一覧へ」「生データを確認」、`CompanyListPage`の各種ボタン等）を`Button`に置き換える。
リンク的な「戻る」ボタン（`← 企業一覧へ`等のテキストリンク）は`Button`化せず、
現状の`text-sm text-gray-500`のまま維持する（ボタンというよりナビゲーションのため）。

### 4.4 レイアウト幅

- `CompanyDetailPage.tsx`：`max-w-3xl` → `max-w-6xl`
- `CompanyFactsPage.tsx`：`max-w-4xl` → `max-w-6xl`
- `DownloadPage.tsx`・`CompanyListPage.tsx`：`max-w-xl` → `max-w-2xl`
- `Header`・`Footer`の`max-w-5xl`は維持

### 4.4b レスポンシブ・2列グリッド

Tailwindの`xl:`（1280px）ブレークポイントを使い、`grid grid-cols-1 xl:grid-cols-2 gap-6`
で対になるセクションを並べる。新規コンポーネントは作らず、`CompanyDetailPage.tsx`・
`CompanyListPage.tsx`側でグリッドラッパーを直接使う（対象がこの2画面に限定されるため、
共通コンポーネント化は今回は行わない）。

- **企業詳細画面**：
  - B/S（`FinancialMetricSection`）とP/L（`FinancialMetricSection`）を1つの
    `grid grid-cols-1 xl:grid-cols-2 gap-6`で並べる
  - キャッシュフロー計算書は対がないため、グリッドの外（前後どちらか）に単独で
    フル幅のまま配置する
  - 財務分析指標の4カテゴリ（収益性・効率性・安全性・投資指標）も同様に
    `grid grid-cols-1 xl:grid-cols-2 gap-6`で2列×2行に並べる
- **企業一覧画面**：企業カードの`<ul>`を`grid grid-cols-1 xl:grid-cols-2 gap-3`に変更する
  （現状は`space-y-2`の縦積みリスト）

`Panel`コンポーネント自体は幅を持たない（親のグリッド/フレックスに従う）ため、
2列化によるPanel自体の変更は不要。

### 4.5 空状態・ローディング表示

`読み込み中...`等の素のテキスト表示を、`<div className="flex justify-center py-16
text-gray-500">`で中央寄せする共通パターンに統一する（新規コンポーネント化はせず、
各ページの該当箇所にクラスを追加するのみ。パターンが単純なため、コンポーネント化は
オーバーエンジニアリングと判断）。

### 4.6 フォント

`index.css`にGoogle Fontsから`Inter`（欧文）・`Noto Sans JP`（和文）を読み込み、
`body`に適用する：

```css
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=Noto+Sans+JP:wght@400;500;700&display=swap');

body {
  font-family: "Inter", "Noto Sans JP", -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
}
```

既存のTailwindユーティリティ（`font-medium`・`font-semibold`等）はそのまま使えるため、
コンポーネント側の変更は不要。

### 4.7 グラフの軸ラベル簡略化

`frontend/src/lib/formatFiscalYear.ts`（新規）に`toFiscalYearAxisLabel(fiscalYear: string):
string`を追加し、`fiscal_year`文字列（例："2021年3月期"）の先頭の年部分だけを正規表現
（`/^(\d+)年/`）で取り出す。`FinancialChart`・`CashFlowChart`・`RatioCategoryChart`の
`<XAxis dataKey="fiscal_year" />`に`tickFormatter={toFiscalYearAxisLabel}`を追加する
（`dataKey`自体は変更しない。Rechartsの`tickFormatter`は軸の表示ラベルのみを変換し、
ツールチップに渡される`label`引数には影響しないため、ツールチップ・表は引き続き
フル表記のままになる）。

---

## 検証方法

1. `tsc -b --noEmit`・`oxlint`が通ることを確認
2. 開発サーバー（vite HMR）で全画面（SCR-001〜004）を表示し、ヘッダー・フッターが
   共通して表示されること、既存の機能（検索・ダウンロード・グラフ表示・トグル）が
   壊れていないことを確認
3. グラフの配色（`CHART_COLORS`等）が変更前と同じであること（値のリファクタリングのみで
   見た目は変えない）を目視確認
4. FR-33：新しい配色（クールブルー）がヘッダー・フッター・ボタン・トグルに反映されて
   いること、`Panel`・`Button`が各画面で正しく表示されること、幅拡大後もレイアウトが
   崩れていないことを目視確認
5. ブラウザウィンドウを1280px以上に広げた際にB/S・P/L、財務分析指標4カテゴリ、
   企業一覧カードが2列表示に切り替わり、それより狭い場合は1列に積まれることを確認
