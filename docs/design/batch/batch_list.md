# バッチ一覧

`backend/scripts/`配下の、手動またはスケジュール実行するバッチ処理のID一覧。
画面（`SCR-XXX`）・API（`API-XXX`）と同様に、新しいバッチを作る前に**必ずこの一覧を
確認し、既存のバッチ・共通モジュールで対応できないか検討する**（似た機能のスクリプトが
多重に作られることを防ぐため）。

| No | バッチID | バッチ名 | 概要 | 実行頻度 | 関連サイクル | ファイル |
|----|---------|---------|------|---------|------------|----------|
| 1 | BATCH-001 | 全上場企業マスタ一括登録 | EDINETコードリストから全上場企業の基本情報を`companies`へ一括登録する | 1回限り（企業マスタが古くなったら再実行を検討） | サイクル6 FR-39 | [BATCH-001_bulk_register_companies.md](BATCH-001_bulk_register_companies.md) |
| 2 | BATCH-002 | バッチ取得タイミング検証 | サンプル企業でダウンロードを実行し、所要時間・EDINETリクエスト数を計測する（検証用） | 検証が必要な時のみ | サイクル7 FR-43、サイクル8 FR-46 | [BATCH-002_verify_batch_timing.md](BATCH-002_verify_batch_timing.md) |
| 3 | BATCH-003 | 書類一覧バックフィル | EDINETの書類一覧APIを日付ごとに呼び、対象書類のメタデータを`documents`へ取り込む（過去分の一括投入・将来の日次実行の両方に使う共通ロジックを呼ぶ） | 1回限り（過去分投入）＋将来は日次（フェーズ4で自動化予定） | サイクル9 FR-49 | [BATCH-003_ingest_document_list.md](BATCH-003_ingest_document_list.md) |
| 4 | BATCH-004 | 書類本体取り込み | `documents`の未取得書類を対象にCSVを取得し`company_quantitative_facts`・`company_qualitative_facts`へ保存する | 定期的（`documents`に未取得書類がある限り実行） | サイクル9 FR-50、サイクル13 FR-58/59 | [BATCH-004_ingest_document_bodies.md](BATCH-004_ingest_document_bodies.md) |
| 5 | BATCH-005 | 企業の定性データ遡及取得 | `company_quantitative_facts`に定量データが取り込み済みの書類を対象にCSVを再取得し、`company_qualitative_facts`を追加保存、`documents.body_ingested_at`も設定する（1回限りの遡及処理） | 1回限り | サイクル13 FR-58・FR-59・FR-60 | [BATCH-005_backfill_qualitative_facts.md](BATCH-005_backfill_qualitative_facts.md) |

---

## 共通モジュール（バッチ本体ではないが複数バッチから使われる）

新しいバッチを作る際は、以下のロジックを重複実装しないこと。

| モジュール | 役割 | 使用バッチ |
|---|---|---|
| `backend/edinet_client.py` | EDINET通信（レート制限・リトライ・キャッシュ込み） | 全バッチ |
| `backend/fact_ingestion.py` | `companies`・`facts`テーブルへの書き込み（`upsert_company`・`upsert_facts`） | BATCH-001（間接）、BATCH-004、`routers/edinet.py`（個別ダウンロードAPI） |
| `backend/document_list_ingestion.py` | 1日分の書類一覧取り込み（`ingest_document_list_for_date`） | BATCH-003 |
| `backend/document_body_ingestion.py` | 1件の書類本体取り込み（`ingest_document_body`） | BATCH-004 |
