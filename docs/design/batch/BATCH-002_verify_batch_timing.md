# BATCH-002 バッチ取得タイミング検証

## 基本情報

| 項目 | 内容 |
|------|------|
| バッチID | BATCH-002 |
| バッチ名 | バッチ取得タイミング検証 |
| ファイル | `backend/scripts/verify_batch_timing.py` |
| 実行方法 | `backend/`ディレクトリで`python -m scripts.verify_batch_timing` |
| 実行頻度 | 検証が必要な時のみ（本番データ投入用ではない、計測用の使い捨てスクリプト） |
| 関連サイクル | サイクル7 FR-43、サイクル8 FR-46（サンプル選定条件の変更） |

## 概要

業種の異なる企業を`SAMPLE_SECTOR_LIMIT`（デフォルト20）件選び、実際に個別ダウンロード
処理（`routers.edinet.run_download_job`）を実行して、1社あたりの所要時間・EDINETへの
リクエスト回数を計測する。IDEA-01フェーズ2〜3の技術検証（EDINET側のレスポンス速度・
リクエスト数の見積もり）のために作成した。

**本バッチ自体は本番のデータ投入手段ではない**（BATCH-004がその役割を担う）。
サンプル企業の実データはこのバッチの実行結果として実際に`company_quantitative_facts`
へ保存されるが、それは計測の副産物であり主目的ではない。

## 入力・出力

| | 内容 |
|---|---|
| 入力 | `companies`テーブル（`accounting_standard IS NULL`＝未取得企業から選定） |
| 出力 | 標準出力への計測ログ（所要時間・リクエスト数・ステータス）。副次的に対象企業の`company_quantitative_facts`が保存される |

## 依存モジュール

- `routers.edinet.run_download_job`・`routers.edinet._states`
- `edinet_client.get_request_count`・`reset_request_count`（サイクル8で追加）

## 実行結果（実績）

- サイクル7（`fetch_document_list`キャッシュ導入前）：20社、合計4,066.5秒・5,100リクエスト
- サイクル8（キャッシュ導入後）：20社、合計2,118.9秒・2,625リクエスト（約48%減）

詳細：[cycle7_batch_timing_estimate.md](../../development/cycle7_batch_timing_estimate.md)
