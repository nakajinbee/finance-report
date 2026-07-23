# サイクル13 要件定義書

対象：[docs/product/use_cases.md](../product/use_cases.md) UC-1-1・UC-1-2・UC-1-3
（大項目1「投資判断のための企業調査」の一部）

**前提確認**：本サイクルはユースケース単位でのサイクル運用（サイクル12で
`cycle-workflow`に追記した方針）に基づく最初のサイクル。UC-1-1・UC-1-2・UC-1-3の
3つの中項目を対象とするが、まとめて設計・実装せず、1つずつ要件定義→設計→実装を
進める（ユーザーの明示的な指示）。本書はまずUC-1-1のみを扱う。UC-1-2・UC-1-3は、
UC-1-1が完了した後、この書に追記する形で進める。

## プロダクト概要（サイクル12までの状況）

サイクル11でコンセプト、サイクル12でユースケース一覧（`docs/product/use_cases.md`）を
確定した。サイクル13から、ユースケース単位（UC-x-x）で画面フロー→画面→API→バッチの
順に設計・実装していく。

## UC-1-1：特定企業の深掘り調査（状態：部分実現）

### 前提確認（企画内容のセルフレビュー）

`docs/design/screen/items/SCR-003_items.md`（画面定義書）を実際のコード
（`frontend/src/pages/CompanyDetailPage.tsx`）と突き合わせたところ、画面定義書が
実装から取り残されていることが判明した：

- 画面定義書は「5指標の棒グラフ1つ」としか書いていないが、実際はB/S・P/Lを
  別々の`FinancialMetricSection`に分けて表示している
- 画面定義書には財務分析指標（サイクル3で追加、収益性・効率性・安全性・投資指標の
  4カテゴリ、`RatioCategorySection`）の記載が一切ない

UC-1-1-1（財務諸表確認）・UC-1-1-2（財務分析指標確認）は実装済みだが、
ドキュメントの是正が必要。

UC-1-1-3（定性情報確認）は未実装。実データで検証した結果、EDINETから既に
取得しているCSV（`fetch_report_csv`の戻り値）の中に、事業の内容
（`jpcrp_cor:DescriptionOfBusinessTextBlock`）・事業等のリスク
（`jpcrp_cor:BusinessRisksTextBlock`）・経営者による財政状態、経営成績及び
キャッシュ・フローの状況の分析（`jpcrp_cor:ManagementAnalysisOfFinancialPositionOperatingResultsAndCashFlowsTextBlock`、
以下MD&A）のテキストブロックが実データとして含まれていることを確認した
（会社コード5971・doc_id S100YR73で実機検証済み）。これまでは数値データのみを
対象にし、テキストブロック行（単位列「－」）を除外していた（cycle1 FR-04）。
**追加のEDINET通信は不要**（既存のCSV取得で完結する）。

## FR-57：SCR-003画面定義書の是正

- `docs/design/screen/items/SCR-003_items.md`を、実際のコード
  （`CompanyDetailPage.tsx`）に合わせて更新する
- 対象：B/S・P/Lの2セクション分離、CF計算書セクション、財務分析指標
  （4カテゴリ：収益性・効率性・安全性・投資指標）セクション
- コードの変更は行わない（ドキュメントのみの是正）

## FR-58：企業の定性データ（事業の内容・事業等のリスク・MD&A）の取得・保存・表示

- 対象テキストブロックは、事業の内容・事業等のリスク・MD&Aの3種類
  （ユーザー確認済み）
- 新テーブル`company_qualitative_facts`（TBL-005）を新設し、書類（doc_id）・
  要素種別（事業の内容/リスク/MD&A）ごとにテキスト本文を保存する
- `xbrl_parser.py`に、CSVからテキストブロック行を抽出する新規関数
  `parse_qualitative_facts`を追加する（既存の`parse_quantitative_facts`
  （後述FR-59でリネーム）とは別関数。対象は上記3要素IDのみに絞り、無関係な
  テキストブロック（表紙情報等）は保存しない）
- `document_body_ingestion.ingest_document_body`を拡張し、企業の定量データ
  （`company_quantitative_facts`）と同じタイミングで定性データも
  `company_qualitative_facts`に保存する（同じCSVを再利用するため、EDINETへの
  追加リクエストは発生しない）
- 新規API（`API-COM-006`）で、指定企業の最新（または期間指定）の定性情報を返す。
  **EDINETには一切アクセスせず、DBのみ参照する**（既存のAPI-COM-002/003/005と
  同じ設計方針、サイクル9で確立した「画面はDBのみ参照」の原則を維持）
- `SCR-003`に定性情報セクションを追加する。長文になるため、開閉可能な形式
  （アコーディオン等）で表示する。年度は財務グラフの年度範囲選択とは独立した
  単一年度セレクタを持ち、初期値は最新年度とする

### 既存データへの遡及適用

現在`facts_ingested_at`が設定済みの書類（515件、83社分）についても、本サイクルで
定性情報を遡及取得する（ユーザーが事前に許可、2026-07-23）。CSVの再取得
（EDINETへの再リクエスト、約515回・約0.6秒間隔で約5分規模）が発生するバッチを
新規に作成し、実行結果を実装セルフレビューに記録する。

## FR-59：既存`facts`テーブル・関連コードの命名是正

UC-1-1のFR-58着手中に、既存の`facts`テーブル名が「定量データである」ことを
名前から読み取れない曖昧な命名であることが判明した（ユーザー指摘）。同時に
新設するテーブルも当初「disclosures」を検討していたが、これも「定性データ」だと
名前から伝わらない曖昧な命名だった。この機会に、両テーブルが対になって
「定量（quantitative）」「定性（qualitative）」を名前だけで判別できるよう、
コード・ドキュメント全体の命名を是正する（ユーザーが「負債になっているから
早めに解消しておこう」と判断、2026-07-23）。

対応表：

| 種別 | 旧 | 新 |
|---|---|---|
| DBテーブル | `facts` | `company_quantitative_facts` |
| DBテーブル（新規） | ―（disclosuresを検討していた） | `company_qualitative_facts` |
| SQLAlchemyモデルクラス | `Fact` | `CompanyQuantitativeFact` |
| SQLAlchemyモデルクラス（新規） | ― | `CompanyQualitativeFact` |
| ファイル | `backend/fact_ingestion.py` | `backend/quantitative_fact_ingestion.py` |
| 関数 | `upsert_facts()` | `upsert_quantitative_facts()` |
| 関数（新規） | ― | `upsert_qualitative_facts()` |
| `xbrl_parser.py`の関数 | `parse_numeric_facts()` | `parse_quantitative_facts()` |
| `xbrl_parser.py`のデータクラス | `NumericFact` | `QuantitativeFact` |
| `xbrl_parser.py`の関数（新規） | ― | `parse_qualitative_facts()` |
| `xbrl_parser.py`のデータクラス（新規） | ― | `QualitativeFact` |
| テーブル定義書 | `TBL-003_facts.md` | `TBL-003_company_quantitative_facts.md` |
| テーブル定義書（新規） | ― | `TBL-005_company_qualitative_facts.md` |
| `documents`テーブルのカラム | `facts_ingested_at` | `body_ingested_at` |
| API-COM-004のパス | `GET /api/companies/{code}/facts` | `GET /api/companies/{code}/quantitative-facts` |
| フロントエンドAPI関数 | `getCompanyFacts()` | `getCompanyQuantitativeFacts()` |
| `companies.py`のローカル変数・型注釈 | `facts`（`list[Fact]`等） | `quantitative_facts`（`list[CompanyQuantitativeFact]`等） |

（2026-07-23追記）当初は関数ローカル変数を対象外にする案を提示したが、
ユーザーの判断で「全部直す」ことになった。`backend/routers/companies.py`内の
`facts`という変数名・`Fact`型注釈も含め、コード全体を一貫してリネームする。

既存テーブル`facts`のリネームはAlembicマイグレーション（`ALTER TABLE facts
RENAME TO company_quantitative_facts`）で行う。`documents.facts_ingested_at`も
同様に`body_ingested_at`へリネームする（この書類の本体〈数値データ・定性データ
双方を含む〉を取り込み済みかを表すカラムのため、特定のテーブル名を含まない
名前にする）。データの中身・行数は変更しない（名前のみの変更）。
`routers/edinet.py`・`document_body_ingestion.py`・`document_list_ingestion.py`・
`scripts/ingest_document_bodies.py`等、影響を受けるすべての呼び出し元を追随して
更新する。

## FR-60：個別ダウンロード機能（SCR-001）がdocumentsテーブルを更新していなかった不整合の是正

BATCH-005（FR-58の遡及バッチ）の対象件数を確認する過程で発見（2026-07-24）。

`company_quantitative_facts`には515件分の書類の定量データが存在するが、
`documents.body_ingested_at`が設定されているのはサイクル9のFR-50サンプル30件のみ
だった。原因は、個別ダウンロード機能（`routers/edinet.py`の`run_download_job`、
SCR-001。サイクル9で`documents`テーブルが新設される前から存在する機能）が、
自前でEDINET書類検索（`search_report`）を行い`company_quantitative_facts`へ
直接書き込むだけで、`documents`テーブルを一切参照・更新していなかったため。
これにより：

- `documents.body_ingested_at`が「書類本体を取り込み済みか」の実態を反映しない
  （485件が実際には取り込み済みなのに未取込と判定される）
- 個別ダウンロードされた書類は定性データ（`company_qualitative_facts`）が
  一切保存されず、今後も個別ダウンロードが使われるたびに同じズレが蓄積する

### 対応

- `run_download_job`が書類を取得した際、`documents`テーブルのレコードを
  作成/更新し、定性データも保存し、`body_ingested_at`を設定するよう修正する
  （`document_list_ingestion.py`の`upsert_document_from_row`を切り出して
  共通化し、`document_body_ingestion.py`と`routers/edinet.py`の両方から使う）
- 過去に個別ダウンロードで取り込み済みの485件は、FR-58のBATCH-005で
  `company_quantitative_facts`の全件（515件）を対象に定性データを遡及取得し、
  あわせて`documents.body_ingested_at`も設定する（ユーザー許可済み、
  2026-07-24。実行時点で新たに2件は個別ダウンロードの実機検証で処理済みのため、
  実際のバッチ対象は485件）

## スコープ外（次サイクル以降）

- UC-1-2（複数企業の比較）・UC-1-3（業界・セクター俯瞰）：UC-1-1完了後に着手
- 定性情報の全文検索・キーワード抽出等の高度な機能（`cycleX_backlog.md`の
  「テキスト開示の保存・検索」の一部はFR-58でカバーされるが、検索機能自体は
  スコープ外）
