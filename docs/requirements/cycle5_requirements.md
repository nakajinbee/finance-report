# サイクル5 要件定義

## プロダクト概要

サイクル4ではヘッダー・フッターやグラフ表示の「器」を仮の配色（クールブルー）で整えたが、
本格的なデザインコンセプトの決定は先送りにしていた。サイクル5では
[design_guideline.md](../design/design_guideline.md)で確定した「モダン分析ツール系」の
デザインコンセプトを実装に反映し、仮決めの状態から本番の見た目に切り替える。

## サイクル5の目標

1. design_guideline.mdで定義した配色・タイポグラフィ・コンポーネントの状態表現を実装に反映する
2. サイクル4の仮のトークン（クールブルー配色）を、design_guideline.mdのブランドトークンに
   置き換える
3. データ取得・グラフのロジック・画面遷移など、デザイン以外の機能には変更を加えない

---

## 機能要件

### FR-34：ブランドカラートークンの入れ替え

- `index.css`の`@theme`に`--color-brand`(`#0D9488`)・`--color-brand-dark`(`#0F766E`)・
  `--color-brand-tint`(`#F0FDFA`)を定義する
- サイクル4で追加した`--color-brand-light`・`--color-tint`トークンは、design_guideline.md
  で使用しないと定義されたため削除する
- `theme.ts`の`THEME`（`accent`・`accentDark`等）は、コードベース中どこからも参照されて
  いない未使用コードであるため、値を更新するのではなく削除する。`CHART_COLORS`・
  `COMPONENT_CHART_COLORS`・`CASH_FLOW_CHART_COLORS`（グラフの系列色）は
  design_guideline.mdの方針通り変更しない

### FR-35：ベース中立色をTailwind標準`gray`スケールへ統一

- サイクル4の独自の背景色・文字色を、`bg-white`／`bg-gray-50`／`text-gray-900`／
  `text-gray-500`／`border-gray-200`に統一する（独自トークンは定義しない）
- `Panel`コンポーネントの背景を`bg-gray-50`にする
- `Header`を白背景＋下部border、`Footer`を`bg-gray-50`背景＋上部borderにする
  （サイクル4の濃紺ヘッダー・seafoam系フッターを置き換える）

### FR-36：フォーム要素・トグル・カードの状態表現

- 入力欄・selectにフォーカス時の見た目（`border-brand` + `ring-2 ring-brand/20`、
  `outline-none`）を追加する
- 入力欄のdisabled状態に`bg-gray-100`・`cursor-not-allowed`を適用する
- `MetricSelector`・`RatioToggle`の選択中／非選択の枠線・背景をブランドトークン
  （`border-brand`・`bg-brand-tint`）に揃える（現状ハードコートされている`border-brand
  bg-sky-50`を置き換える）
- クリック可能なカード（企業一覧のカード等）のホバーは`bg-gray-50`に統一する

### FR-37：数値表示・グラフの装飾統一

- 表の財務数値（金額列）に`font-variant-numeric: tabular-nums`を適用し、桁を縦に揃える
- 各グラフの`CartesianGrid`の`stroke`を`#E5E7EB`（罫線色）に統一する

### FR-38：エラー色・バッジ・アイコン・ローディング表現の確認

- エラーメッセージは標準的な赤（`text-red-600`）のまま変更しない
- 会計基準等のメタ情報はバッジ化せずプレーンテキストのまま変更しない
- アイコンライブラリは導入しない
- ローディング・空状態表示はテキストベースのまま変更しない
- （本FRはdesign_guideline.mdの「現状維持」判断を実装側で崩さないことの確認であり、
  新規の実装作業は発生しない想定）

---

## 非機能要件

### NFR-11：影響範囲

本サイクルの変更はフロントエンドの配色・スタイルのみであり、バックエンド
（API・DB・EDINET連携）には一切変更を加えない。

### NFR-12：既存機能への影響

既存の全画面（SCR-001〜004）の機能（検索・ダウンロード・グラフ表示・指標トグル等）は
変更しない。色・トークン名・一部コンポーネントの背景色・状態表現のみを置き換える。

---

## スコープ外（次サイクル以降）

- アイコンライブラリの導入（design_guideline.mdで「導入しない」と決定済み。恒久的な方針であり
  次サイクル以降も基本的にスコープ外）
- キーボードフォーカスリング（`focus-visible`）等のアクセシビリティ対応
  （design_guideline.mdにTODOとして記載。将来サイクルで検討）
- 企業一覧画面の検索履歴表示、全企業データの一括DB投入・SQLiteからの移行
  （サイクル4から持ち越しのスコープ外事項）
