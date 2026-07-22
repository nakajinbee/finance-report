# サイクル5 開発 セルフレビュー結果

レビュー対象：FR-34〜38（design_guideline.mdの本番デザインコンセプトの実装反映）
レビュー基準：[self_review_rule.md](self_review_rule.md)
設計との対応確認：[docs/design/cycle5_design.md](../design/cycle5_design.md)

---

## 1. 設計の全実装チェック

`git diff`の全差分を設計書のdiffと1件ずつ突き合わせ、内容が一致していることを確認した。

| 設計項目 | 実装箇所 | 状態 |
|---|---|---|
| `--color-brand`/`-dark`/`-tint`の3トークン定義、`--color-brand-light`/`--color-tint`削除 | `index.css` | [x] |
| `THEME`エクスポート削除 | `lib/theme.ts` | [x] |
| `Panel`背景を`bg-gray-50`に | `Panel.tsx` | [x] |
| `Header`を白背景＋下部borderに | `Header.tsx` | [x] |
| `Footer`を`bg-gray-50`＋上部borderに | `Footer.tsx` | [x] |
| トグル選択中を`border-brand bg-brand-tint text-gray-900`に | `MetricSelector.tsx`・`RatioToggle.tsx` | [x] |
| 入力欄・selectのフォーカスリング | `CompanyListPage`・`CompanyDetailPage`・`CompanyFactsPage`・`DownloadPage` | [x] |
| 年度欄disabledに`cursor-not-allowed`追加 | `DownloadPage.tsx` | [x] |
| `body`に`tabular-nums`追加 | `index.css` | [x] |
| `CartesianGrid`の`stroke="#E5E7EB"` | `FinancialChart`・`CashFlowChart`・`RatioCategoryChart` | [x] |
| フォーカス不可の`<div>`・radio/checkboxを対象外のまま変更しない | `DownloadPage.tsx` | [x]（`git diff`に該当箇所の変更がないことを確認） |
| FR-38（現状維持項目）に意図しない変更が入っていないか | `ErrorMessage.tsx`等 | [x]（`git status`にこれらのファイルが含まれていないことを確認） |

`git diff --stat`の変更ファイル数（14）が、設計書§6の変更ファイル一覧と完全に一致することを
確認した。

---

## 2. 動作確認

- [x] `npx tsc -b --noEmit`・`npx oxlint`が通ることを確認（無出力＝エラーなし）
- [x] vite HMRログに実装中〜完了後までエラーが出ていないことを確認
- [x] バックエンド（`GET /api/companies`）・フロントエンド（`/`）双方が`200`で応答することを確認
- [x] コンパイル後のCSS（`curl`で`/src/index.css`取得）を実際に検査し、以下を確認した
  - `--color-brand: #0d9488;`・`--color-brand-dark: #0f766e;`・`--color-brand-tint: #f0fdfa;`
    が定義されていること
  - `bg-brand-tint`・`border-brand:focus`・`ring-brand\/20:focus`・`text-brand:hover`等、
    設計で使うと決めたクラスがTailwindによって実際に生成されていること（クラス名の
    タイポ・存在しないユーティリティの指定がないことの裏取り）
  - `font-variant-numeric: tabular-nums;`が`body`に出力されていること
- [x] 旧トークン・旧ハードコードが残っていないことを`grep`で確認
  （`sky-50`・`brand-light`・`bg-tint`・`border-tint`・`THEME`いずれも0件）
- [ ] ブラウザでの実際の見た目（配色の変化、フォーカスリングの見え方）の目視確認は
  本環境にブラウザ操作ツールがなくできていない。ユーザー側での確認を推奨する

---

## 3. コード品質

- [x] 新規のCSS変数・クラス名はdesign_guideline.mdの命名（`--color-brand`系、
  Tailwind標準`gray`スケール）と一致している
- [x] 未使用コード（`THEME`）を残さず削除した
- [x] 不要なデバッグログなし
- [x] バックエンドの変更なし（NFR-11準拠）。既存機能（検索・ダウンロード・グラフ表示・
  指標トグル等）のロジックに触れていないことを`git diff`で確認（変更はすべて`className`・
  CSS定義のみ）

---

## 判定：テストフェーズ（実機での最終確認）へ移行可能

設計通りに実装済み。設計書のdiffと実装差分を1件ずつ突き合わせ、抜け・過不足は
見つからなかった。コンパイル後のCSSを直接検査し、トークン・ユーティリティクラスが
意図通り生成されていることまで確認済み。ブラウザでの最終見た目確認はユーザー側推奨。

---

## 追記：ユーザーの実機確認で見つかった不具合の修正（`cycle5_design.md`のスコープ外）

サイクル5のデザイン実装後、ユーザーが実際の画面（財務分析指標・B/S・P/L）を確認した際に
3件の不具合が見つかった。いずれも配色・スタイル（FR-34〜37）とは別軸の、既存ロジックの
不具合であり、`cycle5_design.md`には設計されていなかったため、発見都度その場で原因調査・
修正・検証した。

### 1. `RatioCategoryTable`の行順序バグ

**症状**：ROEの行より先に、内訳（純利益・自己資本）の行が表示されていた。
**原因**：`RatioCategoryTable.tsx`で内訳行`newComponents.map(...)`を指標本体の行より前に
描画していた（実装ミス）。
**修正**：指標本体の行を先に、内訳行をその後に描画する順序に入れ替えた。

### 2. 表が選択中の指標だけに絞り込まれていなかった

**症状**：グラフはトグルで選択した指標のみ表示されるのに、その下の表は常に全指標・
全内訳が表示されたままだった（`RatioCategoryTable`・`FinancialMetricTable`の両方）。
**原因**：どちらの表コンポーネントも、トグルの選択状態（`activeKeys`/`activeMetrics`）を
propとして受け取っておらず、渡された`definitions`を無条件に全件描画していた。
**修正**：両コンポーネントに選択状態のpropを追加し、選択中の指標のみ描画するようフィルタした。
内訳行は「親指標が選択されているか」で表示・非表示を決める（内訳自体の個別トグル状態では
判定しない）仕様とした（ユーザー指定）。表の表示条件をチャートと同じ条件分岐にまとめ、
未選択時は表も非表示になるようにした。

### 3. グラフの棒の並び順が選択操作の履歴に依存していた

**症状**：指標を一度選択解除してから再選択すると、その指標の棒グラフが元の位置ではなく
右端に移動していた。
**原因**：`RatioCategoryChart`・`FinancialChart`が、選択中の指標だけを`filter`してから
`<Bar>`をJSXに並べていたため、選択解除時に`<Bar>`がアンマウントされ、再選択時に
別要素として再マウントされていた。Recharts（v3.9.2）はグループ化された棒の並び順を
「現在のJSX宣言順」ではなく「各`<Bar>`が最初にマウントされた順」で内部管理しているため、
再マウントされた`<Bar>`は末尾に追加されていた。
**調査**：Rechartsの型定義・ソース（`node_modules/recharts`）を直接確認し、
`Bar`コンポーネントの`hide`propが「マウントしたまま見た目だけ非表示にし、凡例には
`inactive`として残す」という、まさにこの種のトグルUIのために用意された公式の仕組みで
あることを確認した。また`<Legend>`のデフォルト`itemSorter`が値（ラベル文字列）の
アルファベット順に凡例を並び替える仕様であることも確認した（Recharts v3の型定義
`Legend.d.ts`で確認。誤って"選択順"と見えていたのは実際にはこの凡例側の文字コード順
ソートも影響していた）。
**修正**：全指標の`<Bar>`を常にマウントしたまま`hide={!activeKeys.has(...)}`で
表示・非表示を切り替える方式に変更し、`<Legend itemSorter={null} />`でアルファベット順の
再ソートを止めた。これにより棒・凡例とも定義順（表の順序と同じ）で固定される。
非選択の指標は凡例にグレー表示で残る（Rechartsの`inactive`標準スタイル）。

### 動作確認（追記分）

- [x] `npx tsc -b --noEmit`・`npx oxlint`が通ることを確認（3件の修正すべてで実施）
- [x] vite HMRログを確認。編集途中（片方のファイルだけpropを必須化した瞬間）に
  一過性のエラーが出たが、対応するファイルの編集完了後は解消されていることを確認
  （このプロジェクトで過去にも見られた、複数ファイルにまたがる編集中の既知の挙動）
- [x] バックエンド・フロントエンドが引き続き`200`で応答することを確認
