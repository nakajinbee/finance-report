# TBL-002 financials（財務データ）

> ⚠️ **廃止（サイクル2）**：本テーブルはサイクル2の設計変更（`docs/requirements/cycle2_requirements.md`
> FR-05）により廃止され、[`TBL-003_facts.md`](TBL-003_facts.md)（汎用ファクトテーブル）に
> 置き換えられる。既存データは移行せず、Alembicマイグレーションで本テーブルをDROPする。
> 本ドキュメントはサイクル1の設計記録として残す。

## 基本情報

| 項目 | 内容 |
|------|------|
| テーブルID | TBL-002 |
| テーブル名 | financials |
| 概要 | 企業ごとの期別財務指標を管理する |

---

## カラム定義

| カラム名 | SQLAlchemy 型 | MySQL 型 | NOT NULL | PK | FK | 説明 |
|----------|--------------|----------|----------|----|-----|------|
| id | Integer (AutoIncrement) | INT AUTO_INCREMENT | ✓ | ✓ | | サロゲートキー |
| company_code | String(10) | VARCHAR(10) | ✓ | | companies.code | 証券コード |
| period_end | Date | DATE | ✓ | | | 会計期間終了日（例：2023-03-31） |
| fiscal_year | String(20) | VARCHAR(20) | ✓ | | | 表示用会計年度（例：2023年3月期） |
| revenue | BigInteger | BIGINT | | | | 売上高（円）。データなしの場合 NULL |
| operating_profit | BigInteger | BIGINT | | | | 営業利益（円）。データなしの場合 NULL |
| net_profit | BigInteger | BIGINT | | | | 純利益（円）。データなしの場合 NULL |
| total_assets | BigInteger | BIGINT | | | | 総資産（円）。データなしの場合 NULL |
| total_liabilities | BigInteger | BIGINT | | | | 負債合計（円）。データなしの場合 NULL |

---

## インデックス

| インデックス名 | カラム | 種別 | 目的 |
|--------------|--------|------|------|
| PRIMARY | id | PRIMARY KEY | |
| uq_company_period | company_code, period_end | UNIQUE | 同一企業・同一期のデータ重複防止 |
| idx_company_code | company_code | INDEX | 企業コードでの検索高速化 |

---

## 外部キー制約

| 制約名 | カラム | 参照先 | ON DELETE |
|--------|--------|--------|-----------|
| fk_financials_company | company_code | companies.code | CASCADE |

---

## 備考
- 財務指標は NULL 許容。EDINET のデータに該当科目が存在しない場合は NULL を格納する
- 金額はすべて円単位で格納する。表示時にフロントエンドで億円・兆円に換算する
- BigInteger を使用するのは兆円規模の数値（13桁超）に対応するため
