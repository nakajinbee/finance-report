# SCR-003 企業詳細画面 画面項目定義

親画面：[../SCR-003_company_detail.md](../SCR-003_company_detail.md)

各画面項目が、どのAPI（[api_list.md](../../api/api_list.md)参照）の、どのレスポンス項目から来ているかを定義する。

**2026-07-23（サイクル13）全面是正**：本ドキュメントは長期間、実装（B/S・P/Lの
2セクション分離、経常利益・自己資本の追加、財務分析指標セクションのグラフ化等）に
追随できていなかった。今回、`CompanyDetailPage.tsx`および関連コンポーネントを
実際に読み、現状のコードと一致する内容に全面更新した。あわせて、削除した
SCR-004への遷移ボタン（旧SCR-003-04）を除き、項目IDを詰め直した。

---

## 項目一覧

| 項目ID | 画面項目名 | 表示位置 | 参照元API | 参照元レスポンス項目 | 表示形式・整形ルール | 備考 |
|---|---|---|---|---|---|---|
| SCR-003-01 | 戻るリンク | 画面左上 | なし（画面遷移のみ） | ― | 押下でSCR-002へ遷移 | |
| SCR-003-02 | 企業ヘッダー：企業名 | 画面上部 | API-COM-002 | `CompanyFinancials.company.name` | そのまま表示 | |
| SCR-003-03 | 企業ヘッダー：会計基準 | 画面上部 | API-COM-002 | `CompanyFinancials.company.accounting_standard` | 「会計基準：IFRS」の形式 | `null`の場合「会計基準：データ未取得」 |
| SCR-003-04 | 表示期間選択（開始年度〜終了年度） | ヘッダー下 | API-COM-002 | `CompanyFinancials.company.periods`（選択肢の範囲として使用） | 年セレクタ2つ。選択変更のたびにSCR-003-05〜13をAPI再呼び出しする | SCR-003-14〜19（定性情報）とは連動しない |
| SCR-003-05 | B/S：指標トグル（総資産/負債/自己資本） | B/Sセクション上部 | なし（フロント内処理） | ― | チェックボックス形式、初期状態は全ON | データ自体はSCR-003-06と同じ`data[]`を参照 |
| SCR-003-06 | B/S：グラフ・表（総資産/負債/自己資本） | B/Sセクション | API-COM-002<br>`?from_year=&to_year=` | `data[].total_assets` / `total_liabilities` / `equity` | グループ棒グラフ＋表。円→億円換算。`null`は棒を描画せず「データなし」 | `FinancialMetricSection`（`BS_METRIC_DEFINITIONS`） |
| SCR-003-07 | P/L：指標トグル（売上高/営業利益/経常利益/純利益） | P/Lセクション上部 | なし（フロント内処理） | ― | SCR-003-05と同様 | |
| SCR-003-08 | P/L：グラフ・表（売上高/営業利益/経常利益/純利益） | P/Lセクション | API-COM-002 | `data[].revenue` / `operating_profit` / `ordinary_profit` / `net_profit` | SCR-003-06と同様の整形ルール | `FinancialMetricSection`（`PL_METRIC_DEFINITIONS`）。経常利益はJapan GAAP以外は常に`null` |
| SCR-003-09 | ツールチップ：指標名と金額（B/S・P/L共通） | 棒ホバー時 | API-COM-002 | ホバー中の`data[]`要素における、ONの各指標フィールド | 1兆円以上「X.X兆円」、1兆円未満「X,XXX億円」 | `null`の場合「データなし」 |
| SCR-003-10 | キャッシュフロー：グラフ・表 | CFセクション | API-COM-003<br>`GET /api/companies/{code}/cashflow?from_year=&to_year=` | `CashFlowRecord.operating_cash_flow` / `investing_cash_flow` / `financing_cash_flow` | グループ棒グラフ＋表。SCR-003-09と同じ整形ルール | |
| SCR-003-11 | 財務分析指標：カテゴリセクション×4（収益性/効率性/安全性/投資指標） | 財務分析指標エリア | API-COM-005<br>`GET /api/companies/{code}/ratios?from_year=&to_year=` | `RatioRecord`の該当フィールド（例：収益性→`roe`/`operating_margin`/`net_margin`等） | カテゴリごとにグラフ（棒グラフ）＋表＋内訳トグル | `RatioCategorySection`をカテゴリ定義（`lib/ratioCategories.ts`）ごとに4回使用 |
| SCR-003-12 | 財務分析指標：内訳トグル | 各カテゴリセクション上部 | なし（フロント内処理） | ― | 指標本体（例：ROE）は初期ON、内訳（例：純利益・自己資本）は初期OFF | 2026-07-22ユーザー要望 |
| SCR-003-13 | 財務分析指標：数値の表示形式 | 各カテゴリの表・ツールチップ | API-COM-005 | 各`RatioRecord`フィールド | 比率は%、回転率は「X.X回」、EPS/PERは小数第2位まで | 開示値優先・計算値で補完（サーバー側で確定済み） |
| SCR-003-14 | 事業概要・リスク：セクション見出し | 財務分析指標の後 | なし | ― | 「事業概要・リスク」 | サイクル13新規（FR-58） |
| SCR-003-15 | 事業概要・リスク：年度セレクタ（単一） | セクション上部 | API-COM-006<br>`GET /api/companies/{code}/qualitative-facts` | `available_periods` | 年セレクタ1つ。選択変更のたびにAPI-COM-006を`period_end`指定で再呼び出し | 表示期間選択（SCR-003-04）とは独立。初期値は`available_periods`の最新年度。データなし時は非表示 |
| SCR-003-16 | 事業概要・リスク：事業の内容（開閉式） | セクション内 | API-COM-006 | `business_description` | デフォルト閉、クリックで展開 | `null`の場合は非表示 |
| SCR-003-17 | 事業概要・リスク：事業等のリスク（開閉式） | 同上 | API-COM-006 | `business_risks` | デフォルト閉 | `null`の場合は非表示 |
| SCR-003-18 | 事業概要・リスク：経営者による分析（開閉式） | 同上 | API-COM-006 | `mdanda` | デフォルト閉 | `null`の場合は非表示 |
| SCR-003-19 | 事業概要・リスク：データなし表示 | 同上 | API-COM-006 | ― | 選択年度の3項目とも`null`の場合「この年度の事業概要・リスク情報はありません」 | 開示書類が1件もない場合もパネル自体は常に表示し、年度セレクタなしで「事業概要・リスク情報はありません」と表示する（2026-07-23訂正） |

---

## 画面状態とAPIレスポンスの対応

| 画面状態 | 判定に使うレスポンス項目 |
|---|---|
| ローディング | API-COM-002/003/005/006 呼び出し中（応答待ち） |
| 正常 | API-COM-002 が `200` を返し `data[]` が1件以上 |
| 全指標OFF（B/S・P/L・財務分析指標） | 該当セクションのトグルが全OFF（フロント内状態） |
| データなし（B/S・P/L・財務分析指標） | 対象フィールドが対象期間すべて`null` |
| 事業概要・リスク：年度データなし | API-COM-006の`business_description`/`business_risks`/`mdanda`が全て`null` |
| 事業概要・リスク：データなし（年度セレクタなし） | API-COM-006が`404`（開示書類が1件もない）。パネル自体は表示する |
| エラー | API-COM-002/003/005 が `404`（企業なし）または `500` エラーを返却（`Error`スキーマ） |
