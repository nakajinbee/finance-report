# SCR-001 ダウンロード画面 画面項目定義

親画面：[../SCR-001_download.md](../SCR-001_download.md)

各画面項目が、どのAPI（[api_list.md](../../api/api_list.md)参照）の、どのレスポンス項目から来ているかを定義する。
サイクル2で企業検索（FR-07）・期間指定（FR-09）に対応し、大幅に更新した。

---

## 項目一覧

| 項目ID | 画面項目名 | 表示位置 | 参照元API | 参照元レスポンス項目 | 表示形式・整形ルール | 備考 |
|---|---|---|---|---|---|---|
| SCR-001-01 | 企業検索ボックス | 画面上部 | API-EDN-003<br>`GET /api/edinet/companies/search?q=` | リクエストの`q`パラメータに入力値を渡す | 入力のたびにAPIを呼び出す（デバウンス要） | サイクル2で新規。検索対象はEDINET全上場企業（DB未保存も含む） |
| SCR-001-02 | 検索結果一覧 | 検索ボックス直下 | API-EDN-003 | レスポンス配列`EdinetCompanySearchResult[]`の`name`・`edinet_code`・`sec_code`・`sector` | 一覧表示。クリックで選択確定 | |
| SCR-001-03 | 選択中企業表示 | 検索結果の下 | なし（フロント内状態） | SCR-001-02で選択した`name` | 「選択中：{企業名}」 | |
| SCR-001-04 | 取得期間の指定（全期間／期間指定） | 検索エリアの下 | なし（フロント内状態） | ― | ラジオボタン。期間指定時は開始年・終了年を入力 | サイクル2で新規。値は`POST /api/download`のリクエストボディ`period`にそのまま渡す |
| SCR-001-05 | データ取得ボタン | 中央ボタン | API-EDN-001<br>`POST /api/download` | リクエストボディに`company_code`（選択企業の`sec_code`から4桁化したもの）・`edinet_code`・`period`を送信。レスポンス`status`（`started`固定） | 押下時にAPIを呼び、`202`受信でボタンを非活性化しログエリア表示に遷移 | `409`（同一企業の多重実行）時はエラー表示。企業未選択時はボタン非活性 |
| SCR-001-06 | 取得ログ：各行のアイコン | ログリスト各行の先頭 | API-EDN-002<br>`GET /api/download/status?company_code=` | `logs[].status` | `done`→✓／`in_progress`→⏳／`skipped`→→／`error`→✗ に変換して表示 | 1秒間隔でポーリングして更新。件数は期間指定内容により可変（サイクル1は5件固定だった）。`skipped`はFR-11（既存期間の再ダウンロードスキップ）で追加 |
| SCR-001-07 | 取得ログ：会計年度 | ログリスト各行 | API-EDN-002 | `logs[].fiscal_year` | そのまま文字列表示（例：「2023年3月期」） | |
| SCR-001-08 | 取得ログ：ステータスメッセージ | ログリスト各行 | API-EDN-002 | `logs[].message` | そのまま文字列表示（例：「取得完了」） | |
| SCR-001-09 | 全体進捗判定（ポーリング停止・画面状態切替） | （非表示・内部制御） | API-EDN-002 | トップレベル `status`（`idle`/`in_progress`/`done`/`error`） | `done`または`error`確定でポーリング停止しボタン再活性化 | |
| SCR-001-10 | 企業一覧へボタン | ログエリア下部 | API-EDN-002 | `status == "done"` かつ `logs[]` に1件以上 `status in ("done", "skipped")` を含む | 条件を満たす場合のみ描画。押下でSCR-002へ遷移（API呼び出しなし） | 全件エラー時（`status == "error"`）は非表示。`skipped`は既存データがあるため成功扱い（FR-11） |

---

## 画面状態とAPIレスポンスの対応

| 画面状態 | 判定に使うレスポンス項目 |
|---|---|
| 初期（企業未選択） | ボタン未押下、企業未選択（APIコールなし） |
| 企業選択済み | SCR-001-03の選択状態あり |
| 取得中 | API-EDN-002 `status == "in_progress"` |
| 完了（全件成功） | API-EDN-002 `status == "done"` かつ `logs[]` 全件 `status == "done"` |
| 完了（一部エラー） | API-EDN-002 `status == "done"` かつ `logs[]` に `status == "error"` を含む |
| 完了（全件エラー） | API-EDN-002 `status == "error"` |
