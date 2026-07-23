# サイクル15 実装セルフレビュー

対象：FR-65〜69（[cycle15_requirements.md](../requirements/cycle15_requirements.md)）。

## `git diff`と定義書群の突き合わせ

### バックエンド

- `backend/schemas.py`：`RankingMetric`（Literal、19種類）・`RankingRecord`を追加。
  `RankingRecord.yaml`の項目（`code`・`name`・`sector`・`period_end`・`value`）と一致
- `backend/routers/companies.py`：`GET /companies/ranking`（API-COM-007）を追加。
  `_RANKING_FINANCIAL_METRICS`で財務諸表系・財務分析指標系を判別し、
  `_build_financial_records`・`_build_ratio_records`を再利用して各企業の最新期の
  値を取り出す設計どおりの実装。`metric`が不正な場合は`400`＋`ErrorResponse`
  （`companies_ranking.yaml`の設計どおり）

### フロントエンド

- `frontend/src/api/client.ts`：`RankingMetric`型・`RankingRecord`型・
  `getCompanyRanking()`を追加（`companies_ranking.yaml`のenum19項目と一致）
- `frontend/src/lib/useCompanyFilter.ts`（新規）：SCR-002・SCR-005で共通の
  検索・業種絞り込み・並び順ロジックを抽出。`CompanyListPage.tsx`（SCR-002）は
  この抽出後も動作・見た目とも変更なし（リファクタのみ）であることを
  `tsc`・`oxlint`・vite HMRログで確認した
- `CompanyComparisonSelectPage.tsx`（SCR-005）：SCR-005定義書の機能1〜4を実装。
  カードクリックで選択トグル、除外ボタン、「比較する」ボタンの活性化条件・
  遷移先クエリパラメータ形式（`/compare/result?codes=`）が設計と一致
- `components/comparison/`（新規）：`ComparisonMoneyChart/Table`・
  `ComparisonRatioChart/Table`。SCR-003の`FinancialChart`・`RatioCategoryChart`と
  同じ書式関数（`formatYenForDisplay`・`formatByRatioFormat`）を再利用し、
  x軸を企業名に差し替えた設計どおりの実装
- `CompanyComparisonResultPage.tsx`（SCR-006）：`codes`をクエリパラメータから
  取得し、各企業についてAPI-COM-002/003/005を並行呼び出し。各企業の最新期
  レコード（`period_end`最大）を取り出して7セクション（B/S・P/L・CF・
  収益性・効率性・安全性・投資指標）に表示。一部失敗時の警告表示、空状態の
  リンクも設計どおり
- `CompanyRankingPage.tsx`（SCR-007）：指標未選択時は案内メッセージのみ、
  業種絞り込み・昇順降順切り替え、結果0件メッセージ、行クリックでSCR-003へ
  遷移。SCR-003からの`sector`引き継ぎ（クエリパラメータ）も実装
- `Header.tsx`：「企業比較」「ランキング」のナビリンクを追加（FR-69）
- `App.tsx`：`/compare`・`/compare/result`・`/ranking`ルートを追加
- `CompanyDetailPage.tsx`（SCR-003）：業種の表示、「この企業の業種内での順位を
  見る」リンク（`sector`が`null`でない場合のみ表示）を追加

## 設計からのスコープ調整（実装時に判明した簡略化）

- 比較結果画面（SCR-006）の財務分析指標セクションは、SCR-003のような
  「内訳トグル」（指標本体・内訳の切り替え）は実装していない。FR-66は
  「グラフ・表を表示する」とだけ要求しており、内訳トグルの有無までは
  明記していなかったため、初期スコープとしては指標本体のみの表示とした。
  **定義書側の記述もこの実装に合わせて確認した**（SCR-006定義書・items表は
  最初から「グラフ＋表」のみを要求しており、トグルには言及していないため
  食い違いはない）

## 動作確認

- `npx tsc -b --noEmit`：エラーなし
- `npx oxlint src`：エラーなし（exit 0）
- バックエンド（`uvicorn --reload`）：`routers/companies.py`保存時に自動リロード成功、
  エラーログなし
- `curl`での実データ確認：
  - `GET /api/companies/ranking?metric=revenue` → `200`、トヨタ自動車が1位
    （約50.7兆円）で正しく降順ソートされていることを確認
  - `GET /api/companies/ranking?metric=roe` → `200`、財務分析指標側の分岐も
    正常に動作
  - `GET /api/companies/ranking?metric=revenue&sector=輸送用機器` → `200`、
    業種絞り込みが正しく機能
  - `GET /api/companies/ranking?metric=bogus` → `400`＋`INVALID_METRIC`
- フロントエンド（vite dev server）：`/`・`/compare`・`/ranking`にHTTPリクエストし
  `200`を確認。vite HMRログにエラーなし
- **ブラウザでの実機確認は本セッションで実施できていない**（ブラウザ操作用の
  ツールがない）。次回ブラウザで確認できるタイミングで、以下を必ず確認すること：
  - SCR-005：カードクリックでの選択・解除、選択リストの除外ボタン、
    「比較する」ボタンの活性化・遷移
  - SCR-006：グラフ・表の表示、一部企業のデータ取得失敗時の挙動
  - SCR-007：指標・業種・昇順降順の組み合わせ、行クリックでの遷移
  - SCR-003：「この企業の業種内での順位を見る」リンクでのsector引き継ぎ
  - ヘッダーの「企業比較」「ランキング」リンク

## データ整合性の確認

サイクル15はDBスキーマの新設・変更を行っていない（既存テーブルの参照のみ）ため、
「全削除→再処理」の検証は対象外。

## NFR-15（ランキングAPI応答時間）

[cycle15_design_review.md](../design/cycle15_design_review.md)に実測結果を記録済み
（現状データ量で約4.3秒。全社データ投入後の再検証を`cycleX_backlog.md`へ送った）。

## スコープ外にした事項

- 比較結果画面の財務分析指標セクションの内訳トグル（上記「設計からのスコープ調整」参照）
- ランキングAPIの全社データ投入後の応答時間再検証（`cycleX_backlog.md`に記録済み）

## 結論

設計（定義書群）と実装の内容は一致している。ブラウザでの実機確認のみ未実施のため、
次回確認するまでTODOとして残す。
