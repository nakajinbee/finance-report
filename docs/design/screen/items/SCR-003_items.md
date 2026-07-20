# SCR-003 企業詳細画面 画面項目定義

親画面：[../SCR-003_company_detail.md](../SCR-003_company_detail.md)

各画面項目が、どのAPI（[api_list.md](../../api/api_list.md)参照）の、どのレスポンス項目から来ているかを定義する。
サイクル2で年度範囲指定（FR-12）・キャッシュフロー表（FR-13）に対応し、更新した。

---

## 項目一覧

| 項目ID | 画面項目名 | 表示位置 | 参照元API | 参照元レスポンス項目 | 表示形式・整形ルール | 備考 |
|---|---|---|---|---|---|---|
| SCR-003-01 | 戻るリンク | 画面左上 | なし（画面遷移のみ） | ― | 押下でSCR-002へ遷移。APIは呼ばない | |
| SCR-003-02 | 企業ヘッダー：企業名 | 画面上部 | API-COM-002<br>`GET /api/companies/{code}/financials` | `CompanyFinancials.company.name` | そのまま表示 | |
| SCR-003-03 | 企業ヘッダー：会計基準 | 画面上部 | API-COM-002 | `CompanyFinancials.company.accounting_standard` | 「会計基準：IFRS」の形式で表示 | サイクル2から`IFRS`/`Japan GAAP`/`US GAAP`の3値（実機検証済み） |
| SCR-003-04 | 表示期間選択（開始年度〜終了年度） | ヘッダー下 | API-COM-002 | `CompanyFinancials.company.periods`（選択肢の範囲として使用） | 年セレクタ2つ（開始・終了）。選択変更のたびにSCR-003-06/07とSCR-003-12をAPI再呼び出しする | サイクル1の3期/5期/10期プリセットから変更。API再呼び出しが発生する点もサイクル1と異なる |
| SCR-003-05 | 指標トグルボタン（売上高/営業利益/純利益/総資産/負債合計） | 表示期間選択の下 | なし（フロント内処理） | ― | ON/OFFはフロントの表示状態のみで管理し、グラフに渡すデータ系列を絞り込む | データ自体はSCR-003-06と同じ`data[]`を参照。API再呼び出しなし |
| SCR-003-06 | グラフ：横軸（会計年度） | グラフ下部 | API-COM-002<br>`?from_year=&to_year=` | `data[].fiscal_year` | そのまま表示（例：「2023年3月期」） | |
| SCR-003-07 | グラフ：売上高〜負債合計の棒（5系列） | グラフ本体 | API-COM-002 | `data[].revenue` / `operating_profit` / `net_profit` / `total_assets` / `total_liabilities` | 円→億円に変換して表示（÷100,000,000）。`null`の場合はその期の棒を描画しない | サーバー側はTBL-003 factsから会計基準別マッピングで引き当てる（レスポンス形はサイクル1と同じ） |
| SCR-003-08 | 凡例 | グラフ下部 | なし（フロント内処理） | ― | SCR-003-05でONになっている指標のみ表示 | |
| SCR-003-09 | ツールチップ：指標名と金額 | 棒ホバー時 | API-COM-002 | ホバー中の`data[]`要素における、ONの各指標フィールド | 1兆円以上「X.X兆円」、1兆円未満「X,XXX億円」に整形 | 該当フィールドが`null`の場合は「データなし」と表示 |
| SCR-003-10 | キャッシュフロー表：見出し行（期間） | CF表の1行目 | API-COM-003<br>`GET /api/companies/{code}/cashflow?from_year=&to_year=` | `CashFlowRecord[].fiscal_year` | 表示期間選択（SCR-003-04）と同じ年度範囲 | サイクル2新規（FR-13） |
| SCR-003-11 | キャッシュフロー表：営業/投資/財務CFの3行 | CF表 | API-COM-003 | `CashFlowRecord.operating_cash_flow` / `investing_cash_flow` / `financing_cash_flow` | 円→兆円/億円に変換（SCR-003-09と同じ整形ルール） | `null`の場合は「データなし」 |
| SCR-003-12 | 生データを確認リンク | 画面下部 | なし（画面遷移のみ） | ― | 押下でSCR-004（`/companies/{code}/facts`）へ遷移 | サイクル2新規 |

---

## 画面状態とAPIレスポンスの対応

| 画面状態 | 判定に使うレスポンス項目 |
|---|---|
| ローディング | API-COM-002/003 呼び出し中（応答待ち） |
| 正常 | API-COM-002 が `200` を返し `data[]` が1件以上 |
| 全指標OFF | SCR-003-05の全トグルがOFF（フロント内状態、APIとは無関係。CF表はこの状態でも表示され続ける） |
| データなし | API-COM-002 の `data[]` 全要素で、対象5指標がすべて `null` |
| エラー | API-COM-002/003 が `404`（企業なし）または `500` エラーを返却（`Error`スキーマ） |
