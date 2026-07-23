# BATCH-004 書類本体取り込み

## 基本情報

| 項目 | 内容 |
|------|------|
| バッチID | BATCH-004 |
| バッチ名 | 書類本体取り込み |
| ファイル | `backend/scripts/ingest_document_bodies.py` |
| 実行方法 | `backend/`ディレクトリで`python -m scripts.ingest_document_bodies` |
| 実行頻度 | `documents`に未取得書類がある限り繰り返し実行できる（`SAMPLE_LIMIT`で
  1回の実行件数を制御） |
| 関連サイクル | サイクル9 FR-50、サイクル13で命名是正（FR-59） |

## 概要

`documents`テーブル（BATCH-003が作る索引）から、まだ本体を取り込んでいない書類
（`body_ingested_at IS NULL`かつ`csv_flag='1'`）を対象に、書類取得APIでCSVを取得し、
パースして企業の定量データ（`company_quantitative_facts`）・定性データ
（`company_qualitative_facts`）の両テーブルへ保存する。取り下げられた書類
（`withdrawal_status`が`1`または`2`）は対象外にする。

サイクル9時点では`SAMPLE_LIMIT = 30`（少数サンプルでの動作確認）に絞っている。
全社分を実行する場合は`SAMPLE_LIMIT`を`None`に変更する（次サイクル以降で対応）。

## 入力・出力

| | 内容 |
|---|---|
| 入力 | `documents`テーブル（未取得書類）、EDINET書類取得API |
| 出力 | `company_quantitative_facts`・`company_qualitative_facts`テーブルへの
  INSERT/UPDATE、`documents.body_ingested_at`の更新、（`companies.accounting_standard`が
  未設定の場合）`companies`テーブルの更新 |

## 依存モジュール

- `document_body_ingestion.ingest_document_body`
- `quantitative_fact_ingestion.upsert_company`・`upsert_quantitative_facts`・
  `upsert_qualitative_facts`（`routers/edinet.py`の個別ダウンロードAPIと共用）
- `edinet_client.fetch_report_csv`・`xbrl_parser.parse_quantitative_facts`・
  `xbrl_parser.parse_qualitative_facts`・`xbrl_parser.extract_accounting_standard`

## 備考

- 1件の取得・パースに失敗しても処理全体は止めず、次の書類に進む（例外を捕捉しログに残す）
- `routers/edinet.py`の個別ダウンロードAPIとは別経路だが、DBへの書き込みロジック
  （`quantitative_fact_ingestion`）は完全に共通化されている。同じロジックを重複実装しない
- サイクル13で`company_qualitative_facts`への保存も同じタイミングで行うように
  拡張した（追加のEDINET通信は発生しない、既存のCSV取得を再利用）
