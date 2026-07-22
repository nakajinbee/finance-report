# BATCH-003 書類一覧バックフィル

## 基本情報

| 項目 | 内容 |
|------|------|
| バッチID | BATCH-003 |
| バッチ名 | 書類一覧バックフィル |
| ファイル | `backend/scripts/ingest_document_list_backfill.py` |
| 実行方法 | `backend/`ディレクトリで`python -m scripts.ingest_document_list_backfill` |
| 実行頻度 | 1回限り（過去`BACKFILL_YEARS`年分に追いつくため）。追いつき後の日次実行の
  自動化はフェーズ4（次サイクル以降）で対応 |
| 関連サイクル | サイクル9 FR-49 |

## 概要

EDINETの書類一覧APIは日付を指定してその日の全提出書類を返す設計であり、企業を指定して
取得する機能を持たない。この設計に沿い、今日から1日ずつ過去`BACKFILL_YEARS`
（デフォルト10）年分遡り、対象書類（有価証券報告書・半期報告書、証券コードを持つ企業）の
メタデータを`documents`テーブル（TBL-004）へ記録する。

1日分の取り込みロジックは`document_list_ingestion.ingest_document_list_for_date`に
独立しており、本バッチ（過去分の一括投入）にも、将来の日次実行（フェーズ4）にも
同じ関数を使う。

## 入力・出力

| | 内容 |
|---|---|
| 入力 | EDINET書類一覧API（`edinet_client.fetch_document_list`） |
| 出力 | `documents`テーブルへのINSERT/UPDATE |

## 再開機能

途中で停止した場合（通信の瞬断等）、再実行すると`documents`に記録済みの最も古い
`list_date`の1日前から再開する（今日からやり直さない。サイクル9実装中に実際に
通信タイムアウトで停止した経験を踏まえて追加）。

## 依存モジュール

- `document_list_ingestion.ingest_document_list_for_date`
- `edinet_client.fetch_document_list`・`to_company_code`（内部で使用）

## 備考

- 対象を有価証券報告書・半期報告書、かつ証券コードを持つ企業に限定して保存する
  （大量保有報告書・ファンドの書類等は保存しない。YAGNI）
- `edinet_client._get`には通信の一時的な瞬断（`ConnectionError`/`Timeout`）に対する
  リトライ（最大3回、5秒間隔）が入っている（サイクル9でBATCH-003実行中に追加）
