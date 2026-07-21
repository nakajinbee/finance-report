# サイクル3 開発 セルフレビュー結果

レビュー対象：FR-17（候補element_idマッピング化）・FR-18（非連結コンテキストフォールバック）・
FR-19（決算日「N月末日」対応）の実装
レビュー基準：[self_review_rule.md](self_review_rule.md)
設計との対応確認：[docs/design/cycle3_design.md](../design/cycle3_design.md)
ドメイン知識との整合性確認：[docs/domain/xbrl_tagging_variability.md](../domain/xbrl_tagging_variability.md)

---

## 1. 設計の全実装チェック

| 設計項目 | 実装箇所 | 状態 |
|---|---|---|
| `METRIC_CONTEXT_ID`・候補リスト化された`FIVE_METRICS`/`CASH_FLOW` | `backend/metric_mappings.py` | [x] 実装済み |
| `_local_name`・`_index_facts_by_period`・`_lookup_metric` | `backend/routers/companies.py` | [x] 実装済み |
| `_build_financial_records`/`_build_cash_flow_records`の新ロジックへの置き換え | 同上 | [x] 実装済み |
| `FISCAL_YEAR_END_LAST_DAY_OF_MONTH`センチネル・`_parse_fiscal_year_end`拡張 | `backend/edinet_client.py` | [x] 実装済み |
| `_resolve_fiscal_year_end_day`・`fiscal_year_end_date` | 同上 | [x] 実装済み |
| 全呼び出し箇所（`determine_latest_available_fiscal_year`・`fiscal_year_start`・
  `half_fiscal_year_end`・`report_search_center`・`routers/edinet.py`の`_expected_period_end`）の
  `fiscal_year_end_date()`経由への置き換え | `edinet_client.py`・`routers/edinet.py` | [x] 実装済み（grepで旧`date(year, month, day)`直書きが残っていないことを確認済み） |

データフロー・エラー処理（候補なし→データなし、未知の決算日表記→既存動作維持）は
設計書通りに実装されている。カスタマイズ設定は本サイクルの対象外（設計書通り）。

---

## 2. 動作確認

### 正常系（実データ、[cycle3_company_verification.md](../requirements/cycle3_company_verification.md)の10社で確認）

- [x] リクルートHD・任天堂・野村HD（サイクル2で検証済みの3社）が実装変更後も同じ値を返す
  （NFR-07：回帰確認）
- [x] トヨタ自動車の売上高が取得できる（企業固有拡張タグのローカル名フォールバック）。
  実際にサーバーを起動し`POST /api/download`→`GET /api/companies/7203/financials`まで
  実行し、`revenue: 48036704000000`が返ることをE2Eで確認済み
- [x] 大本組の5指標・CF3項目すべてが取得できる（非連結コンテキストフォールバック）
- [x] 良品計画（決算日「8月末日」）がダウンロードできる。実際にサーバーを起動し
  `POST /api/download`→`GET /api/download/status`まで実行し、`2025年8月期`
  （有価証券報告書）・`2025年2月期（半期）`の両方が`done`になることをE2Eで確認済み
  （月末決算の解決ロジックが、FR-08の半期報告書ロジックとも正しく組み合わさることを確認）
- [x] 正興電機製作所・太陽化学・フジックス・武田薬品工業（元々問題なかった4社）が
  実装変更後も同じ値を返す

### 異常系

- [x] 候補が1つも見つからない場合に「データなし」（`None`）になるか　→ 野村HDの
  `operating_profit`・`total_liabilities`が引き続き`None`になることを確認済み
  （サイクル2から意図的に許容している既知の欠落、FR-20で対象外と明記）
- [ ] 「N月末日」「N月N日」以外の未知の決算日表記が実際に来た場合の挙動　→
  コードパス上は変更前と同じ`(None, None)`を返すことをコードレビューで確認したが、
  该当する実企業データでの実地確認はできていない（今回の机上検証では該当企業が
  見つからなかったため）
- [ ] EDINET APIエラー時・ネットワーク切断時の挙動　→ 本サイクルでは変更していない箇所のため
  再確認していない（サイクル2のレビューで確認済み）

---

## 3. コード品質

- [x] APIキー・秘密情報のハードコードなし（変更箇所に該当なし）
- [x] ユーザー入力のサニタイズ（本サイクルは新規の外部入力を追加していないため対象外）
- [x] 型ヒントを使っているか　→ `_local_name`・`_index_facts_by_period`・`_lookup_metric`・
  `fiscal_year_end_date`・`_resolve_fiscal_year_end_day`すべて型ヒント付き
- [x] 不要なデバッグログ（`print`等）を削除しているか　→ `grep`で確認、該当なし
- [x] 名前が機能を表しているか　→ `_lookup_metric`（何を検索するか明確）、
  `FISCAL_YEAR_END_LAST_DAY_OF_MONTH`（センチネル値の意味が名前から分かる）等
- [x] 日付・時刻が[date_format_policy.md](date_format_policy.md)通りか　→
  `fiscal_year_end_date`は`datetime.date`を返し、`datetime.datetime`との混在なし

---

## ドメイン知識・設計との整合性確認

設計セルフレビュー（[cycle3_design_review.md](../design/cycle3_design_review.md)）で発見した
「`consolidated_or_individual`列は連結・非連結の判別に使えない」という訂正が、実装
（`_lookup_metric`のdocstring）にも正しく反映されていることを確認した。実装がコンテキストIDの
`_NonConsolidatedMember`サフィックスのみで判別しており、`consolidated_or_individual`列を
判別ロジックに一切使っていないことをコードレビューで確認済み。

---

## 追記（2026-07-22）：未実施だった4項目の対応

前回レビューで「未実施」としていた4項目について、順番に対応した。

### 1. FR-20：US GAAP指標カバレッジ拡充の追加調査
オリックス（証券コード8591）を追加検証。野村HDと同一パターン（`operating_profit`・
`total_liabilities`は連結US GAAPベースの要素が存在しない）であることを確認。個別
（非連結、日本基準ベース）の値は存在するが会計概念が異なるため代替しない方針を確定。
コード変更なし（`metric_mappings.py`に候補を追加しない、という意思決定のみ）。

### 2. 未知の決算日表記の実地確認
EDINETコードリスト全件（11,353件）を実機スキャンし、`N月N日`・`N月末日`の2パターン
以外の表記が存在しないことを確認（空文字列6,216件を除き100%カバー）。コード変更は
コメントの事実誤り訂正（"－"→空文字列）のみ。

### 3. オムニ・プラス・システム・リミテッドの404エラー原因調査 → FR-21として修正
探索窓が実行日（本日）より未来の日付に達すると、EDINET側が`metadata.status="404"`を
返し、`search_report`のループが異常終了することが原因と特定した。`search_report`で
未来日を候補から除外するよう修正。修正前後で同じ企業を実行し、修正後は
`EdinetDocumentNotFoundError`（正常な「見つからない」判定）に変わることを確認済み。
リクルートHDでの回帰確認（変更前と同じdocIDが返る）も実施済み。

### 4. EDINET APIエラー時の異常系再確認 → FR-22を発見・修正
無効なAPIキーで実際に`fetch_document_list`を実行し、401エラー時のレスポンス形状が
他のエラー（400/404/500）と異なる（`metadata`でラップされない）ことを発見した。
既存コードはこの形状を判定できず、`status=None, message=unknown error`という
不明瞭なメッセージになっていた（エラーとしては検知できていたためシステムクラッシュは
なかったが、原因が伝わらない状態だった）。`_get`に401専用の判定を追加し、
`EdinetAuthError`という明確な例外を送出するよう修正。修正後、同じ手順で
`EDINET APIキーが無効です: Access denied due to invalid subscription key...`という
明確なメッセージになることを確認済み。有効なAPIキーでの通常フロー（ZIPレスポンス）に
回帰がないことも確認済み。

---

## 追記（2026-07-22）：FR-23〜26（財務分析指標の拡充）の実装セルフレビュー

### 1. 設計の全実装チェック
| 設計項目 | 実装箇所 | 状態 |
|---|---|---|
| `DISCLOSED_RATIOS`・`BALANCE_SHEET_ITEMS`・関連コンテキストID定数 | `backend/metric_mappings.py` | [x] |
| `_safe_div`・`_build_ratio_records` | `backend/routers/companies.py` | [x] |
| `GET /companies/{code}/ratios`（API-COM-005） | 同上 | [x] |
| `RatioRecord`スキーマ | `backend/schemas.py` | [x] |
| `RatioRecord`型・`getCompanyRatios` | `frontend/src/api/client.ts` | [x] |
| `formatPercentForDisplay`・`formatTurnoverForDisplay`・`formatNumberForDisplay` | `frontend/src/lib/formatRatio.ts` | [x] |
| `RatioSection`コンポーネント | `frontend/src/components/RatioSection.tsx` | [x] |
| SCR-003への組み込み（CF表の下、新セクション） | `frontend/src/pages/CompanyDetailPage.tsx` | [x] |

### 2. 動作確認
- [x] 10社の実データで`_build_ratio_records`を検証（後述の不具合修正後、全社で妥当な値を確認）
- [x] ユーザーが実際にダウンロード済みのリクルートHDの本番相当データ（2018年3月期〜2026年3月期、
  12期分）で`GET /api/companies/6098/ratios`を実行し、複数年にわたって妥当な値
  （ROE 12.6%〜19.3%等）が返ることを確認。一部の古い年度で`equity_ratio`・`current_ratio`等が
  `null`になるケースも確認したが、該当年度のfactsに元々該当タグが存在しないためで、
  想定通りの「データなし」挙動
- [x] `tsc -b --noEmit`・`oxlint`が通ることを確認
- [x] 開発中のuvicorn（`--reload`）・vite（HMR）で変更が自動反映され、実行中のアプリで
  そのまま動作することを確認
- [ ] ブラウザでの実際の表示（RatioSectionのレイアウト崩れ等）は、本環境にブラウザ操作
  ツールがなく目視確認できていない。ユーザー側での確認を推奨する

### 3. コード品質
- [x] 型ヒント・TypeScript型定義を完備
- [x] 命名：`_safe_div`（ゼロ除算処理であることが名前から分かる）、`RatioKey`（TypeScript側で
  `Exclude`により`fiscal_year`/`period_end`を除外した型安全なキー集合にしている）

### 発見した不具合と修正
**`_index_facts_by_period`が全ての値を`int()`で丸めていたため、ROE（0.163等）のような
1未満の小数がすべて`0`になっていた。** 5指標・CF3項目（すべて整数の円単位）ではこれまで
問題にならなかったが、比率指標の追加で顕在化した。値を`float`のまま保持し、金額系
（`FinancialRecord`・`CashFlowRecord`）はPydanticの自動型変換で従来通り`int`として
扱われることを確認した上で修正。10社の財務指標・キャッシュフローで回帰がないことを
再確認済み。

### ドメイン知識との整合性確認
`docs/domain/xbrl_tagging_variability.md` 6節（開示値・計算値の二重存在）と、
`_build_ratio_records`の`equity_ratio = disclosed.get("equity_ratio") or _safe_div(...)`
という実装が一致していることを確認した。

---

## 判定：テストフェーズ（実機での最終確認）へ移行可能

サイクル3で残っていた4項目、および追加要望（財務分析指標の拡充）に対応し、
実機検証・回帰確認を完了した。ブラウザでの最終目視確認のみユーザー側推奨。
