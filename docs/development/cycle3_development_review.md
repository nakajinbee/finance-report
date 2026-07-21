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

## 判定：テストフェーズ（実機での最終確認）へ移行可能

未実施の異常系確認（未知の決算日表記の実地確認、EDINET APIエラー時の再確認）は、
該当する事例が現時点で見つかっていない・サイクル2で確認済みのため、本サイクルでは
許容範囲とする。将来、未知の決算日表記を持つ企業が見つかった場合は、
`docs/domain/xbrl_tagging_variability.md`に追記した上で個別対応する。
