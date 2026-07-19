# フロントエンド実装方針

`docs/design/cycle1_design.md`（技術スタック：React + TypeScript / React Router v6 / Recharts）を
実装レベルまで具体化したメモ。実装を始める前の技術選定の記録として残す。

---

## ビルド・言語

| 項目 | 方針 | 理由 |
|---|---|---|
| ビルドツール | Vite | Create React Appは公式に非推奨化済み。React公式もViteを案内しており、3画面のみのSPAには十分 |
| 言語 | TypeScript（設計書どおり） | 既に決定済み |
| パッケージ管理 | npm | Node標準同梱。追加ツール（pnpm/yarn）は今回の規模では恩恵が薄いため見送り |

---

## フレームワーク・ライブラリ構成

| レイヤー | 採用技術 | 備考 |
|---|---|---|
| UIライブラリ | React | 設計書どおり |
| ルーティング | React Router v6 | `/download`・`/companies`・`/companies/:code`（SCR-001〜003） |
| グラフ描画 | Recharts（`BarChart`） | SCR-003の指標グラフに使用 |
| スタイリング | **Tailwind CSS** | ユーティリティクラスで高速にスタイリング。指標カラー（`#4E79A7`等、SCR-003参照）はTailwindのカスタムカラーとして`tailwind.config`に定義する |
| HTTP通信 | 標準`fetch` | 呼び出すAPIは4本のみ（`docs/design/api/api_list.md`参照）。axios等の追加ライブラリは導入しない |
| Lint | ESLint（Viteテンプレート標準構成） | 導入する |
| Format | Prettier | ESLintと併用し、フォーマットルールの衝突を避けるため`eslint-config-prettier`を併せて入れる |
| テスト | 現時点では未導入 | バックエンド同様、画面数・ロジックが増えた段階で導入を検討する |

---

## ディレクトリ構成（`cycle1_design.md`準拠）

```
frontend/
├── src/
│   ├── App.tsx                          # Router設定
│   ├── pages/
│   │   ├── DownloadPage.tsx             # SCR-001
│   │   ├── CompanyListPage.tsx          # SCR-002
│   │   └── CompanyDetailPage.tsx        # SCR-003
│   ├── components/
│   │   ├── FinancialChart.tsx           # グラフ（SCR-003-06〜13）
│   │   ├── MetricSelector.tsx           # 指標切り替え（SCR-003-05）
│   │   └── ErrorMessage.tsx             # エラー表示
│   ├── api/
│   │   └── client.ts                    # fetchラッパー。api_list.mdのAPI-EDN-*/API-COM-*に対応する関数を定義
│   └── index.css                        # Tailwindのエントリポイント
├── tailwind.config.js
├── postcss.config.js
├── .eslintrc / eslint.config.js
├── .prettierrc
├── vite.config.ts
├── tsconfig.json
└── package.json
```

---

## 実装順序

1. **Vite雛形作成**（`npm create vite@latest frontend -- --template react-ts`）＋ Tailwind/ESLint/Prettierセットアップ
2. **`api/client.ts`** — `docs/design/screen/items/SCR-*_items.md`で確定した型（`Company`/`CompanyFinancials`/`DownloadStatus`等）をTypeScript型として定義し、fetch関数を実装。バックエンドの`openapi.yaml`のレスポンス形と1対1になるようにする
3. **`pages/`** — 画面定義書（SCR-001〜003）と画面項目定義書（`items/SCR-*_items.md`）どおりに実装。項目IDごとの参照元APIレスポンスフィールドをそのまま使う
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

## 未決事項（実装中に必要になったら決める）

- 開発時のバックエンドAPIのモック方法（MSW導入 or Viteのproxy設定でバックエンドに直接つなぐか）
- CORS：バックエンド側（`backend_implementation_policy.md`）の未決事項と対になる。Viteのdevサーバーのポート（デフォルト5173）を前提にバックエンド側のCORS許可オリジンを決める
