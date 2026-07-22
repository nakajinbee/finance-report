# サイクル5 設計書

対象：[cycle5_requirements.md](../requirements/cycle5_requirements.md) FR-34〜38
デザインの値そのものの根拠：[design_guideline.md](design_guideline.md)

実装順：FR-34（トークン定義）→ FR-35（ベース中立色）→ FR-36（状態表現）→ FR-37（数値・
グラフ装飾）→ FR-38（現状維持項目の確認、コード変更なし）

---

## 1. FR-34：ブランドカラートークンの入れ替え

### `frontend/src/index.css`

```css
@import url("https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=Noto+Sans+JP:wght@400;500;700&display=swap");
@import "tailwindcss";

@theme {
  --color-brand: #0d9488; /* メイン（ボタン・リンク・選択状態） */
  --color-brand-dark: #0f766e; /* ホバー・強調 */
  --color-brand-tint: #f0fdfa; /* 淡い背景（選択中トグルの背景等） */
}

body {
  font-family:
    "Inter",
    "Noto Sans JP",
    -apple-system,
    BlinkMacSystemFont,
    "Segoe UI",
    sans-serif;
}
```

サイクル4の`--color-brand-light`・`--color-tint`トークンは削除する（design_guideline.mdで
不使用と決定済み、参照箇所はFR-35でHeader/Footerの書き換えと同時に消える）。

### `frontend/src/lib/theme.ts`

`THEME`オブジェクト（`background`・`surface`・`border`・`textPrimary`・`textSecondary`・
`accent`・`accentDark`・`accentLight`・`tint`）は、コードベース中どこからも参照されていない
（`grep`で確認済み）。ベース中立色はTailwind標準`gray`クラスを直接使い、アクセント色は
`index.css`の`--color-brand`系トークンを`bg-brand`等のクラス経由で使うため、この定数を
経由する設計にはしない。**`THEME`エクスポートを削除する**（未使用コードの整理、FR-34の
スコープ内）。

`CHART_COLORS`・`COMPONENT_CHART_COLORS`・`CASH_FLOW_CHART_COLORS`は`lib/metrics.ts`・
`lib/ratioCategories.ts`・`CashFlowChart.tsx`から参照されており、変更しない
（design_guideline.mdの「グラフの配色」方針通り）。

---

## 2. FR-35：ベース中立色をTailwind標準`gray`スケールへ統一

### `frontend/src/components/Panel.tsx`

```diff
- className={`rounded-lg border border-gray-200 bg-white p-6 shadow-sm ${className ?? ""}`}
+ className={`rounded-lg border border-gray-200 bg-gray-50 p-6 shadow-sm ${className ?? ""}`}
```

### `frontend/src/components/layout/Header.tsx`

```tsx
export function Header() {
  return (
    <header className="border-b border-gray-200 bg-white">
      <div className="mx-auto flex max-w-5xl items-center justify-between px-8 py-4">
        <Link to="/companies" className="text-lg font-semibold text-gray-900">
          企業会計情報
        </Link>
        <Link to="/companies" className="text-sm text-brand hover:text-brand-dark">
          企業一覧
        </Link>
      </div>
    </header>
  );
}
```

`bg-brand-dark`（濃紺）→`bg-white`＋`border-b border-gray-200`、文字色`text-white`→
`text-gray-900`、リンク色`text-brand-light`→`text-brand`（ホバーは`text-brand-dark`を追加）
に変更する。

### `frontend/src/components/layout/Footer.tsx`

```tsx
export function Footer() {
  return (
    <footer className="border-t border-gray-200 bg-gray-50">
      <div className="mx-auto max-w-5xl px-8 py-4 text-sm text-gray-500">
        データ出典：EDINET（金融庁）
      </div>
    </footer>
  );
}
```

`border-brand-light/40 bg-tint`→`border-gray-200 bg-gray-50`、文字色`text-brand-dark`→
`text-gray-500`（サブテキスト色）に変更する。

他のページ（`CompanyDetailPage`・`CompanyFactsPage`・`CompanyListPage`・`DownloadPage`）は
サイクル4の時点ですでに`text-gray-900`・`text-gray-500`・`bg-white`等のTailwind標準クラスを
使っており、変更不要（`grep`で確認済み）。

---

## 3. FR-36：フォーム要素・トグル・カードの状態表現

### 入力欄・select（フォーカス・disabled）

対象：`CompanyListPage.tsx`（検索欄）、`CompanyDetailPage.tsx`（年度select×2）、
`CompanyFactsPage.tsx`（要素IDフィルタ・期間select）、`DownloadPage.tsx`（対象企業検索欄・
年度欄×2）。`DownloadPage.tsx`の「選択中：〇〇」を表示する`<div>`（188行目、
`border border-gray-300`が付いているがフォーカス不可の静的な表示枠）は対象外とする。

既存の共通パターン`"rounded border border-gray-300 px-2 py-1"`（サイズ違いのバリエーションを
含む）に、フォーカス用のクラスを追記する：

```diff
- className="rounded border border-gray-300 px-3 py-2"
+ className="rounded border border-gray-300 px-3 py-2 outline-none focus:border-brand focus:ring-2 focus:ring-brand/20"
```

`DownloadPage.tsx`の年度欄（229〜238行目）はすでに`disabled:bg-gray-100`を持っているが、
`disabled:cursor-not-allowed`が付いていないため追加する：

```diff
- className="w-20 rounded border border-gray-300 px-2 py-1 disabled:bg-gray-100"
+ className="w-20 rounded border border-gray-300 px-2 py-1 disabled:cursor-not-allowed disabled:bg-gray-100"
```

他の入力欄はdisabled状態を持たないため、disabled用クラスの追加は不要（FR-36の
「disabled状態に`bg-gray-100`・`cursor-not-allowed`を適用する」は、disabled状態を持つ
要素に適用するという規定であり、disabled状態自体を持たない要素に強制するものではない）。

### 対象外：ラジオボタン（`DownloadPage.tsx`の取得期間選択、211〜224行目）

`<input type="radio">`はブラウザ標準の見た目のまま変更しない。design_guideline.mdは
入力欄・select・トグル・ボタンの状態表現を定義しているが、ネイティブのradio/checkboxには
言及がなく、本サイクルのスコープに含めない（次サイクル以降、必要になった時点で
design_guideline.mdに追記した上で対応する）。

### `frontend/src/components/MetricSelector.tsx`・`RatioToggle.tsx`

```diff
- isActive ? "border-brand bg-sky-50" : "border-gray-200 text-gray-400"
+ isActive ? "border-brand bg-brand-tint text-gray-900" : "border-gray-200 text-gray-400"
```

サイクル4の暫定実装で残っていた`bg-sky-50`（Tailwind標準の水色、トークン化されていない
ハードコード）を、新トークン`bg-brand-tint`に置き換える。選択中の文字色は指定していなかった
ため、design_guideline.md通り`text-gray-900`を明示する。2ファイルとも同一の変更。

### `frontend/src/pages/CompanyListPage.tsx`（企業カードのホバー）

現状すでに`hover:bg-gray-50`が適用済み（サイクル4で実装済み）。design_guideline.mdの
「カード（クリック可能な場合）」ルールと一致しており、変更不要。

---

## 4. FR-37：数値表示・グラフの装飾統一

### 財務数値の`tabular-nums`

対象：`FinancialMetricTable.tsx`・`RatioCategoryTable.tsx`・`CashFlowTable.tsx`の数値セル
（`text-right`が付いている`<td>`）、および`CompanyFactsPage.tsx`の値列（189行目）。

個別のクラス追加ではなく、`index.css`の`body`に`font-variant-numeric: tabular-nums`を
追加し、アプリ全体の数字表示に一律適用する（財務系アプリでは数値以外のテキストに
`tabular-nums`が適用されても表示上の副作用がないため、要素ごとに指定して回るより
確実で漏れがない）：

```css
body {
  font-family: ...; /* 既存のまま */
  font-variant-numeric: tabular-nums;
}
```

### `CartesianGrid`の`stroke`

対象：`FinancialChart.tsx`・`CashFlowChart.tsx`・`RatioCategoryChart.tsx`

```diff
- <CartesianGrid strokeDasharray="3 3" />
+ <CartesianGrid strokeDasharray="3 3" stroke="#E5E7EB" />
```

3ファイルとも同一の変更。`#E5E7EB`はTailwindの`gray-200`と同じ値（`border-gray-200`との
統一）。Rechartsの`stroke`プロパティはCSS変数を直接解釈しないため、ここは16進数値を
そのまま指定する。

---

## 5. FR-38：現状維持項目の確認

以下はdesign_guideline.mdで「現状維持」と決定済みであり、コード変更は発生しない：

- エラーメッセージ（`ErrorMessage.tsx`）：`text-red-600`のまま
- 会計基準の表示（`CompanyListPage.tsx`・`CompanyDetailPage.tsx`）：プレーンテキストのまま
- アイコン：導入しない（矢印はテキストの`←`のまま）
- ローディング・空状態：テキスト表示のまま
- グラフのツールチップ：`ChartTooltip`系コンポーネントの白背景・`shadow`のまま

実装フェーズでは、これらのファイルに意図せず変更が入っていないことを最終確認する
（差分に含まれていたら設計外の変更として指摘する）。

---

## 6. 変更ファイル一覧

| ファイル | 変更内容 | 関連FR |
|---|---|---|
| `frontend/src/index.css` | ブランドトークン差し替え、`tabular-nums`追加 | FR-34, FR-37 |
| `frontend/src/lib/theme.ts` | `THEME`エクスポート削除 | FR-34 |
| `frontend/src/components/Panel.tsx` | 背景色を`bg-gray-50`に変更 | FR-35 |
| `frontend/src/components/layout/Header.tsx` | 白背景ヘッダーに変更 | FR-35 |
| `frontend/src/components/layout/Footer.tsx` | `bg-gray-50`フッターに変更 | FR-35 |
| `frontend/src/components/MetricSelector.tsx` | 選択中スタイルをブランドトークンに | FR-36 |
| `frontend/src/components/RatioToggle.tsx` | 同上 | FR-36 |
| `frontend/src/pages/CompanyListPage.tsx` 他、入力欄を持つ4ページ | フォーカス時クラス追加 | FR-36 |
| `frontend/src/components/FinancialChart.tsx`・`CashFlowChart.tsx`・`RatioCategoryChart.tsx` | `CartesianGrid`の`stroke`指定 | FR-37 |
