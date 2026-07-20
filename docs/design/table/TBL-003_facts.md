# TBL-003 facts（財務ファクトテーブル）

## 基本情報

| 項目 | 内容 |
|------|------|
| テーブルID | TBL-003 |
| テーブル名 | facts |
| 概要 | EDINETから取得した数値データを、要素単位で汎用的に保持する（TBL-002 financialsの後継） |

サイクル1の`financials`テーブル（5指標固定カラム）を廃止し、「1行＝1事実（要素ID＋値の組み合わせ）」
という汎用形式に置き換える（`docs/requirements/cycle2_requirements.md` FR-05）。
CSVの構造（要素ID・項目名・コンテキストID・連結個別・期間時点・ユニット・単位・値）を
ほぼそのまま保持することで、新しい指標が欲しくなってもテーブル変更やEDINETへの
再アクセスなしに対応できる。

---

## カラム定義

| カラム名 | SQLAlchemy 型 | MySQL 型 | NOT NULL | PK | FK | 説明 |
|----------|--------------|----------|----------|----|-----|------|
| id | Integer (AutoIncrement) | INT AUTO_INCREMENT | ✓ | ✓ | | サロゲートキー |
| company_code | String(10) | VARCHAR(10) | ✓ | | companies.code | 証券コード |
| doc_id | String(8) | VARCHAR(8) | ✓ | | | EDINET書類管理番号（例：`S100YDHL`）。トレーサビリティ用 |
| doc_type_code | String(3) | VARCHAR(3) | ✓ | | | 書類種別コード。`120`=有価証券報告書（年次）、`160`=半期報告書（FR-08） |
| period_end | Date | DATE | ✓ | | | 会計期間終了日 |
| element_id | String(255) | VARCHAR(255) | ✓ | | | 要素ID（例：`jpcrp_cor:RevenueIFRSSummaryOfBusinessResults`） |
| element_name | String(255) | VARCHAR(255) | | | | 項目名の日本語ラベル（例：`売上収益（IFRS）、経営指標等`） |
| context_id | String(100) | VARCHAR(100) | ✓ | | | 原CSVのコンテキストID（例：`CurrentYearDuration`） |
| consolidated_or_individual | String(20) | VARCHAR(20) | | | | CSVの「連結・個別」列の値（例：`その他`、`個別`） |
| period_or_instant | String(10) | VARCHAR(10) | | | | CSVの「期間・時点」列の値（`期間`または`時点`） |
| unit | String(20) | VARCHAR(20) | | | | 単位（例：`円`、`pure`）。CSVの「単位」列 |
| value | Numeric | DECIMAL(30,4) | ✓ | | | 数値データの値。テキストブロック（単位が`－`の行）はFR-04により
取り込み対象外のため、valueは常に数値が入る想定 |

---

## インデックス

| インデックス名 | カラム | 種別 | 目的 |
|--------------|--------|------|------|
| PRIMARY | id | PRIMARY KEY | |
| uq_company_doc_element_context | company_code, doc_id, element_id, context_id | UNIQUE | 同一書類の再取込による重複防止 |
| idx_company_element | company_code, element_id | INDEX | 画面表示・分析クエリでの指標絞り込み用（例：特定企業の売上高だけ取り出す） |
| idx_company_period | company_code, period_end | INDEX | 年度範囲指定（FR-12）でのクエリ高速化用 |

---

## 外部キー制約

| 制約名 | カラム | 参照先 | ON DELETE |
|--------|--------|--------|-----------|
| fk_facts_company | company_code | companies.code | CASCADE |

---

## 備考

- **集計済みキャッシュテーブルは今回作らない**（`cycle2_requirements.md` FR-05、YAGNI）。
  画面表示・分析クエリが実際に遅くなった場合のみ、別途キャッシュ層を検討する
- **`value`の型はNumeric（DECIMAL）とし、BigIntegerは使わない**：TBL-002では金額が常に
  整数（円単位）だったためBigIntegerで十分だったが、TBL-003は比率（例：ROE=`0.310`）や
  1株当たり指標（例：EPS=`349.78`）など小数を含む値も保存するため、小数対応が必須
- 会計基準（`companies.accounting_standard`）の表記は、EDINETのDEI要素
  （`jpdei_cor:AccountingStandardsDEI`）の値をそのまま保存する（`"IFRS"` / `"Japan GAAP"` /
  `"US GAAP"`、実機検証済み。`docs/domain/会計基準/会計基準の基礎知識.md`参照）。
  正規化・変換レイヤーは設けない（YAGNI、素の値で困る場面が出たら検討する）
- サイクル1で保存済みの`financials`テーブルのデータは移行しない（FR-05）。
  マイグレーション（Alembic）で`financials`テーブルをDROPし、`facts`テーブルをCREATEする
- サイクル1では`companies`テーブルは1社（リクルートHD）固定だったが、サイクル2からは
  企業検索（FR-07）により複数社の行が入る。`companies`テーブル自体のカラム構成は
  変更不要（TBL-001のまま）
