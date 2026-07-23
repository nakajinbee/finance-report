# TBL-005 company_qualitative_facts（企業の定性データテーブル）

## 基本情報

| 項目 | 内容 |
|------|------|
| テーブルID | TBL-005 |
| テーブル名 | company_qualitative_facts |
| 概要 | EDINETの提出本文書CSVに含まれる定性データ（事業の内容・事業等のリスク・MD&A）のテキストブロックを保持する（サイクル13新設、UC-1-1） |

[TBL-003 company_quantitative_facts](TBL-003_company_quantitative_facts.md)（定量データ）と
対になるテーブル。数値の代わりに、同じCSVに含まれる長文のテキスト記載（単位列が
「－」の行）を保持する。数値と異なりCSVを解析する時点で対象要素を絞り込む
（3種類のみ）ため、`company_quantitative_facts`のような汎用要素テーブルにはせず、
対象要素を列として持つ設計にはしない（要素種別ごとに1行、`element_id`で区別する
形にする。将来対象要素が増える可能性を考慮し、列を固定せず行を追加する形にした）。

追加のEDINET通信は発生しない。`document_body_ingestion.ingest_document_body`が
`company_quantitative_facts`を保存するのと同じCSV（既に取得済み）から抽出する。

---

## カラム定義

| カラム名 | SQLAlchemy 型 | MySQL 型 | NOT NULL | PK | FK | 説明 |
|----------|--------------|----------|----------|----|-----|------|
| doc_id | String(8) | VARCHAR(8) | ✓ | ✓ | documents.doc_id | EDINET書類管理番号 |
| element_id | String(100) | VARCHAR(100) | ✓ | ✓ | | テキストブロックの要素ID。`jpcrp_cor:DescriptionOfBusinessTextBlock`（事業の内容）・`jpcrp_cor:BusinessRisksTextBlock`（事業等のリスク）・`jpcrp_cor:ManagementAnalysisOfFinancialPositionOperatingResultsAndCashFlowsTextBlock`（MD&A）のいずれか |
| company_code | String(10) | VARCHAR(10) | ✓ | | companies.code | 証券コード（`documents.company_code`と同じ値を非正規化して保持。クエリの簡便化のため） |
| period_end | Date | DATE | | | | 対象期間（至）。`documents.period_end`と同じ値を非正規化して保持 |
| content | Text | TEXT | ✓ | | | テキストブロックの本文（EDINET CSVの「値」列をそのまま保持） |

---

## インデックス

| インデックス名 | カラム | 種別 | 目的 |
|--------------|--------|------|------|
| PRIMARY | doc_id, element_id | PRIMARY KEY | 1書類につき最大3行（対象要素の数） |
| idx_company_qualitative_facts_company_period | company_code, period_end | INDEX | 「この企業の指定年度の定性情報」を取得するクエリ（API-COM-006）を高速化 |

---

## 外部キー制約

| 制約名 | カラム | 参照先 | ON DELETE |
|--------|--------|--------|-----------|
| fk_company_qualitative_facts_document | doc_id | documents.doc_id | CASCADE |
| fk_company_qualitative_facts_company | company_code | companies.code | CASCADE |

---

## 備考

- **対象要素を3種類に限定する理由（YAGNI）**：EDINET CSVには表紙情報等、他にも
  多数のテキストブロック要素が含まれるが、UC-1-1が必要とする「事業の内容・
  リスク・MD&A」の3種類のみを保存する。不要な要素まで保存すると行数・
  データ量が肥大化するため、`xbrl_parser.parse_qualitative_facts`側で対象要素を
  絞り込む
- **`company_quantitative_facts`との関係**：`documents`と同様、
  `company_quantitative_facts`とは直接の外部キー関係を持たない（`doc_id`は
  共通だが、テーブルの関心が異なる）
- **既存データへの遡及適用**：本テーブル新設時点で既に`body_ingested_at`が
  設定済みの書類（515件）についても、`BATCH-005`（遡及バッチ）でCSVを再取得し
  定性データを追加保存する（`company_quantitative_facts`・`documents`は変更しない）
- **命名の経緯**：当初「disclosures」という名称を検討していたが、「定性データで
  あることが名前から伝わらない」という指摘を受け、`company_quantitative_facts`
  （定量データ）と対になる`company_qualitative_facts`（定性データ）という名称に
  最初から決定した（サイクル13）
