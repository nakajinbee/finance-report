# サイクル13 開発 セルフレビュー結果（UC-1-1）

レビュー対象：FR-57・FR-58・FR-59・FR-60（UC-1-1：特定企業の深掘り調査）
レビュー基準：[self_review_rule.md](self_review_rule.md)
設計との対応確認：[docs/design/cycle13_design.md](../design/cycle13_design.md)

---

## 1. 設計の全実装チェック

| 設計項目 | 実装箇所 | 状態 |
|---|---|---|
| FR-57：SCR-003画面定義書の是正 | `docs/design/screen/SCR-003_company_detail.md`・`items/SCR-003_items.md` | [x] |
| FR-58：`CompanyQualitativeFact`モデル・マイグレーション | `backend/database.py`・`alembic/versions/25652cfde874_*.py` | [x] |
| FR-58：`parse_qualitative_facts`・`upsert_qualitative_facts` | `backend/xbrl_parser.py`・`quantitative_fact_ingestion.py` | [x] |
| FR-58：`document_body_ingestion`拡張 | `backend/document_body_ingestion.py` | [x] |
| FR-58：`API-COM-006` | `backend/routers/companies.py`・`schemas.py` | [x] |
| FR-58：定性情報セクション（年度セレクタ・開閉式3項目） | `frontend/src/pages/CompanyDetailPage.tsx`・`components/QualitativeFactSection.tsx` | [x] |
| FR-58：BATCH-005遡及バッチ | `backend/scripts/backfill_qualitative_facts.py` | [x]（実行済み、485件・全件成功） |
| FR-59：`facts`→`company_quantitative_facts`等の命名是正 | `backend/database.py`・`xbrl_parser.py`・`quantitative_fact_ingestion.py`・`routers/companies.py`・`routers/edinet.py`・`alembic/versions/1dcd7dd744e4_*.py` | [x] |
| FR-60：`run_download_job`のdocuments連携修正 | `backend/routers/edinet.py`・`document_list_ingestion.py`（`upsert_document_from_row`切り出し） | [x] |

`git status`の変更・新規ファイルが設計書§7の一覧と一致することを確認した。

---

## 2. 動作確認（実データで検証、モックなし）

### リネーム（FR-59）
- [x] マイグレーション実行後、`company_quantitative_facts`が482,692行のまま
  （データ欠損なし）であることを確認
- [x] `GET /api/companies`・`/financials`・`/cashflow`・`/ratios`・
  `POST /api/download`（会社コード6098）がリネーム後も正常応答することを確認

### 定性データ（FR-58）
- [x] 会社コード5971・1301で`GET /api/companies/5971(1301)/qualitative-facts`が
  正しい定性データ・`available_periods`（1301は10年分）を返すことを確認
- [x] 定性データが存在しない企業（会社コード6098）で`404`
  `QUALITATIVE_FACTS_NOT_FOUND`を確認
- [x] フロントエンド：`tsc -b --noEmit`エラーなし。ユーザーによる実機確認
  スクリーンショットで、年度セレクタ・開閉式3項目の表示・句点改行を確認
- [x] BATCH-005実行結果：485件対象、成功485件・失敗0件

### 根本原因修正（FR-60）
- [x] 未ダウンロードの会社コード1376で`POST /api/download`を実行し、
  `documents`にレコードが新規作成され`body_ingested_at`が設定されること、
  `company_qualitative_facts`にも正しく保存されることを確認
- [x] BATCH-005実行後、`documents.body_ingested_at`が設定済みの件数（517件）と
  `company_quantitative_facts`のdistinct doc_id数（517件）が完全一致することを
  確認し、不整合が解消されたことを検証した

---

## 3. 発見事項（設計スコープ外で見つかった不具合・追加対応）

### 3.1 SCR-004（生データ確認画面）・API-COM-004の削除

UC-1-1の設計・実装を進める中で、ユーザーからSCR-004（保存済みデータ確認画面）が
「ユースケースに紐づかない開発者向け機能」と判断され、削除の指示があった。
対応するフロントエンドページ（`CompanyFactsPage.tsx`）・APIエンドポイント
（`API-COM-004`）・関連ドキュメント（画面定義書・API定義書・スキーマ）を
すべて削除した。

### 3.2 定性データの命名是正（FR-59追加）

当初`disclosures`という仮称で設計していた新テーブルについて、ユーザーから
「facts」も「disclosures」も中身が名前から読み取れない曖昧な命名だと指摘があり、
既存の`facts`テーブルも含めて`company_quantitative_facts`／
`company_qualitative_facts`という対になる名前に是正した（変数名・クラス名・
ファイル名・APIパスまで全面的にリネーム）。

### 3.3 個別ダウンロード機能とdocumentsテーブルの不整合（FR-60追加、最も重要な発見）

BATCH-005（FR-58の遡及バッチ）の対象件数を確認する過程で、
`company_quantitative_facts`には515件分の定量データがあるのに、
`documents.body_ingested_at`が設定されているのは30件だけという食い違いを発見した。
原因は、個別ダウンロード機能（`routers/edinet.py`の`run_download_job`、
SCR-001。`documents`テーブルが新設されたサイクル9より前から存在する機能）が
`documents`テーブルを一切更新していなかったため。この状態を放置すると、
今後も個別ダウンロードが使われるたびに定性データが保存されず、
`body_ingested_at`のズレも蓄積し続ける状態だった。

`document_list_ingestion.py`から`upsert_document_from_row`を切り出して共通化し、
`run_download_job`でも`documents`レコードの作成/更新・定性データ保存・
`body_ingested_at`設定を行うよう修正した。実データ（会社コード1376）で動作確認済み。
BATCH-005側も対象を`company_quantitative_facts`基準に修正し、
過去分485件の`body_ingested_at`も設定した。

### 3.4 定性データの表示品質の制約（対応せず、backlogへ）

EDINETの書類取得API`type=5`（CSV）は、元テキストに表が含まれる場合、
CSV変換時点で区切り文字を失い数字が連結してしまう既知の制約があることを実機で
発見した。句点ごとの改行では改善しない。`type=1`（元のXBRL/インラインXBRL）を
使えば改善する可能性が高いが実装規模が大きいため、`cycleX_backlog.md`へ送り、
本サイクルでは対応しない（ユーザー判断）。

---

## 4. コード品質

- [x] 型ヒントを完備（`CompanyQuantitativeFact`・`CompanyQualitativeFact`とも）
- [x] `upsert_document_from_row`の切り出しにより、書類一覧取り込みと個別
  ダウンロードでロジックの重複がない
- [x] リネームによりテーブル・クラス名から定量/定性の区別が名前だけで伝わるように
  なった（`facts`単体の曖昧な命名を解消）
- [x] 不要なデバッグログなし

---

## 5. スコープ外事項（`cycleX_backlog.md`へ追記済み）

- 定性データの表示品質改善（`type=1`のXBRL/インラインXBRLからの再抽出）
- UC-1-2（複数企業の比較）・UC-1-3（業界・セクター俯瞰）：次サイクル以降

---

## 判定：完了

FR-57〜60すべて設計通りに実装し、実データで動作確認済み。実装中に2件の重要な
発見（命名是正の追加スコープ、個別ダウンロード機能の`documents`不整合）があり、
いずれもその場で要件定義・設計に反映し対応した。特にFR-60は、放置していれば
今後も蓄積し続けるアーキテクチャ上の不整合であり、UC-1-1の実装中に発見・修正
できたことは大きな成果だった。UC-1-1（特定企業の深掘り調査）は全小項目
（財務諸表・財務分析指標・定性情報）が実現済みとなった。
