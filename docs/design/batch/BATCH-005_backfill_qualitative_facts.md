# BATCH-005 企業の定性データ遡及取得

## 基本情報

| 項目 | 内容 |
|------|------|
| バッチID | BATCH-005 |
| バッチ名 | 企業の定性データ遡及取得 |
| ファイル | `backend/scripts/backfill_qualitative_facts.py` |
| 実行方法 | `backend/`ディレクトリで`python -m scripts.backfill_qualitative_facts` |
| 実行頻度 | 1回限り（過去分の定性データを追いつかせるため） |
| 関連サイクル | サイクル13 FR-58・FR-59・FR-60 |

## 概要

`company_quantitative_facts`に既に定量データが取り込み済みの書類（515件）のうち、
`documents.body_ingested_at`が未設定の書類（＝定性データがまだ保存されていない
書類）を対象に、CSVを再取得して`company_qualitative_facts`を追加保存し、
`documents.body_ingested_at`も設定する。

対象を`documents.body_ingested_at`ではなく`company_quantitative_facts`の
distinct doc_idを基準にしている理由：個別ダウンロード機能（SCR-001、
`routers/edinet.py`）が長年`documents`テーブルを更新していなかったため
（FR-60参照）、`body_ingested_at`だけを見ると実際に取り込み済みの書類
（485件）を見落としてしまう。

## 入力・出力

| | 内容 |
|---|---|
| 入力 | `company_quantitative_facts`（対象書類の判定）、`documents`（`body_ingested_at`の判定・更新対象）、EDINET書類取得API |
| 出力 | `company_qualitative_facts`テーブルへのINSERT/UPDATE、`documents.body_ingested_at`の更新 |

## 依存モジュール

- `xbrl_parser.parse_qualitative_facts`
- `quantitative_fact_ingestion.upsert_qualitative_facts`

## 備考

- `company_quantitative_facts`・`documents`の他のカラムは変更しない
  （`body_ingested_at`のみ更新）
- 1件の取得・パースに失敗しても処理全体は止めず、次の書類に進む
- 実行前にユーザーへ許可確認済み（約485件・約0.6秒間隔で約5分規模、2026-07-24。
  当初515件を想定していたが、実機検証中の個別ダウンロードで2件が先行処理済みの
  ため実際の対象は485件）
