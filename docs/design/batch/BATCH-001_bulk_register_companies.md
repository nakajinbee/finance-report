# BATCH-001 全上場企業マスタ一括登録

## 基本情報

| 項目 | 内容 |
|------|------|
| バッチID | BATCH-001 |
| バッチ名 | 全上場企業マスタ一括登録 |
| ファイル | `backend/scripts/bulk_register_companies.py` |
| 実行方法 | `backend/`ディレクトリで`python -m scripts.bulk_register_companies` |
| 実行頻度 | 1回限り想定（企業マスタ（EDINETコードリスト）が大きく変わった場合の再実行はありうるが、
  現時点で定期実行の仕組みはない） |
| 関連サイクル | サイクル6 FR-39 |

## 概要

EDINETコードリスト（`EdinetcodeDlInfo.csv`）から、証券コードを持つ企業（＝上場企業）
すべての基本情報（企業名・証券コード・業種）を`companies`テーブルへ一括登録する。
財務データ（`accounting_standard`）はこの時点では設定しない（`NULL`のまま）。

## 入力・出力

| | 内容 |
|---|---|
| 入力 | EDINETコードリスト（`edinet_client.list_all_filers()`経由、既存キャッシュを利用） |
| 出力 | `companies`テーブルへのINSERT/UPDATE（証券コードを4桁に変換した`code`をキーにする） |

## 処理内容

1. `edinet_client.list_all_filers()`で全提出者を取得
2. `sec_code`を持たない提出者（ファンド等）はスキップ
3. `edinet_client.to_company_code()`で証券コード（5桁）を`companies.code`（4桁）へ変換
4. 既存企業があれば`name`・`sector`を更新、なければ新規作成（`accounting_standard`は
   触らない＝既存の値を上書きしない）
5. 1件の処理でエラーが起きてもスキップしてログに残し、全体は止めない

## 依存モジュール

- `edinet_client.list_all_filers`・`edinet_client.to_company_code`

## 実行結果（実績）

2026-07-22実行：3,829件登録/更新、sec_codeなしで7,522件スキップ、エラー0件。
