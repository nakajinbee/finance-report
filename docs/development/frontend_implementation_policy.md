# フロントエンド実装方針

`docs/design/cycle1_design.md`（技術スタック：React + TypeScript / React Router v6 / Recharts）を
実装レベルまで具体化したメモ。実装を始める前の技術選定の記録として残す。

---

## ビルド・言語

| 項目 | 方針 | 理由 |
|---|---|---|
| ビルドツール | Vite | Create React Appは公式に非推奨化済み。React公式もViteを案内しており、3画面のみのSPAには十分 |
| 言語 | TypeScript（設計書どおり） | 既に決定済み |
| パッケージ管理 | **pnpm** | npmはサプライチェーン攻撃・脆弱性の懸念があるとの判断で見送り。pnpmは厳密な依存解決でフラットdependency問題が起きにくく、近年npmの代替として広く使われている |

---

## フレームワーク・ライブラリ構成

| レイヤー | 採用技術 | 備考 |
|---|---|---|
| UIライブラリ | React 19 | 設計書どおり |
| ルーティング | React Router v7 | `/download`・`/companies`・`/companies/:code`・`/companies/:code/facts`（SCR-001〜004）。共通の`Layout`（`Header`/`Footer`）が`Outlet`で各ページを描画する（サイクル4で導入） |
| グラフ描画 | Recharts v3（`BarChart`） | SCR-003・SCR-004の各グラフに使用 |
| スタイリング | **Tailwind CSS v4** | `@tailwindcss/vite`プラグイン方式。ブランドカラー（`--color-brand`等）は`index.css`の`@theme`にCSS変数として定義し、Tailwindのユーティリティクラス（`bg-brand`等）から参照する。グラフの系列色（`CHART_COLORS`等）はTailwindではなく`lib/theme.ts`のTypeScript定数で管理する（Rechartsに直接渡す値のため）。詳細は[design_guideline.md](../design/design_guideline.md) |
| HTTP通信 | 標準`fetch` | 呼び出すAPIは8本（EDN系3本＋COM系5本、`docs/design/api/api_list.md`参照）。axios等の追加ライブラリは導入しない |
| Lint | ESLint（Viteテンプレート標準構成） | 導入する |
| Format | Prettier | ESLintと併用し、フォーマットルールの衝突を避けるため`eslint-config-prettier`を併せて入れる |
| テスト | 現時点では未導入 | バックエンド同様、画面数・ロジックが増えた段階で導入を検討する |

---

## ディレクトリ構成（`cycle1_design.md`準拠）

```
frontend/
├── src/
│   ├── main.tsx                         # エントリポイント
│   ├── App.tsx                          # Router設定（Layoutでラップ）
│   ├── pages/
│   │   ├── DownloadPage.tsx             # SCR-001
│   │   ├── CompanyListPage.tsx          # SCR-002
│   │   ├── CompanyDetailPage.tsx        # SCR-003
│   │   └── CompanyFactsPage.tsx         # SCR-004（サイクル2で追加）
│   ├── components/
│   │   ├── layout/
│   │   │   ├── Layout.tsx               # Header/Footer＋Outlet（サイクル4）
│   │   │   ├── Header.tsx
│   │   │   └── Footer.tsx
│   │   ├── Panel.tsx                    # 共通カードコンポーネント（サイクル4）
│   │   ├── Button.tsx                   # 共通ボタンコンポーネント（サイクル4）
│   │   ├── FinancialChart.tsx / FinancialMetricTable.tsx / FinancialMetricSection.tsx  # B/S・P/L
│   │   ├── RatioCategoryChart.tsx / RatioCategoryTable.tsx / RatioCategorySection.tsx / RatioToggle.tsx  # 財務分析指標（サイクル3）
│   │   ├── CashFlowChart.tsx / CashFlowTable.tsx
│   │   ├── MetricSelector.tsx           # B/S・P/L指標の切り替え
│   │   └── ErrorMessage.tsx             # エラー表示
│   ├── lib/
│   │   ├── theme.ts                     # グラフ系列色（CHART_COLORS等）の定数
│   │   ├── metrics.ts / ratioCategories.ts  # 指標定義（キー・ラベル・色・計算元コンポーネント）
│   │   ├── formatCurrency.ts / formatRatio.ts / formatFiscalYear.ts  # 表示用フォーマッタ
│   │   └── kana.ts                      # 企業名検索の読み仮名正規化
│   ├── api/
│   │   └── client.ts                    # fetchラッパー。api_list.mdのAPI-EDN-*/API-COM-*に対応する関数を定義
│   └── index.css                        # Tailwindのエントリポイント＋@theme（ブランドトークン）＋フォント設定
├── eslint.config.js
├── .prettierrc
├── vite.config.ts                        # @tailwindcss/vite プラグインを含む
├── tsconfig.json
├── package.json
└── pnpm-lock.yaml
```

Tailwind CSS 4系は`@tailwindcss/vite`プラグイン方式のため、`tailwind.config.js`・
`postcss.config.js`は不要（`vite.config.ts`にプラグイン追加＋CSSに1行importするのみ）。

---

## 実装順序

1. **Vite雛形作成**（`npm create vite@latest frontend -- --template react-ts`）＋ Tailwind/ESLint/Prettierセットアップ
2. **`api/client.ts`** — `docs/design/screen/items/SCR-*_items.md`で確定した型（`Company`/`CompanyFinancials`/`DownloadStatus`等）をTypeScript型として定義し、fetch関数を実装。バックエンドの`openapi.yaml`のレスポンス形と1対1になるようにする
3. **`pages/`** — 画面定義書（SCR-001〜004）と画面項目定義書（`items/SCR-*_items.md`）どおりに実装。項目IDごとの参照元APIレスポンスフィールドをそのまま使う
4. **`components/`** — グラフ・指標切り替え等の共通コンポーネントを切り出す

バックエンド（`docs/development/backend_implementation_policy.md`）のAPI層が動く前に、
フロントは`api/client.ts`をモックレスポンスで先行実装してもよい（並行開発可能）。

---

## コーディング方針

- コンポーネント・関数名はPascalCase/camelCase、TypeScriptの型は極力`openapi.yaml`のスキーマ名（`Company`・`FinancialRecord`等）に合わせる。`any`は使わず明示的な型を付ける
- コンポーネント・関数・変数の名前は、そのユースケースや機能が読んで分かる名前にする（`data`・`temp`のような汎用名は避け、`formatYenToOku`のように「何をするか」が伝わる名前にする）
- 金額の円→億円変換、兆円/億円の表示切り替え（SCR-003-07〜13）はユーティリティ関数として`components`外に切り出し、テスト可能な形にしておく（将来テスト導入時に備える）
- 日付・会計年度の表記は[date_format_policy.md](date_format_policy.md)に従う（`fiscal_year`は`period_end`から動的生成せずAPIの値をそのまま表示する等）
- コメントは「WHY」のみ。JSXの構造で「WHAT」が伝わるようにする

---

## 解決済みの旧未決事項

- **開発時のバックエンドAPIのモック方法**：モックは使わない。実際に`uvicorn main:app`を起動し、
  フロントから`http://localhost:8000`へ直接HTTP接続する（プロジェクト全体の「実データ・実APIで検証する」方針に合わせた）
- **CORS**：バックエンド側`main.py`で`http://localhost:5173`（Viteのデフォルトポート）を
  許可済み（`backend_implementation_policy.md`参照）
