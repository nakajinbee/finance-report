# TBL-001 companies（企業マスタ）

## 基本情報

| 項目 | 内容 |
|------|------|
| テーブルID | TBL-001 |
| テーブル名 | companies |
| 概要 | EDINET から取得した企業の基本情報を管理する |

---

## カラム定義

| カラム名 | SQLAlchemy 型 | MySQL 型 | NOT NULL | PK | 説明 |
|----------|--------------|----------|----------|----|------|
| code | String(10) | VARCHAR(10) | ✓ | ✓ | 証券コード（例：6098） |
| name | String(255) | VARCHAR(255) | ✓ | | 企業名（例：リクルートホールディングス） |
| sector | String(100) | VARCHAR(100) | | | 業種（例：サービス業）。EDINETの業種区分 |
| accounting_standard | String(50) | VARCHAR(50) | ✓ | | 会計基準（IFRS / JapaneseGAAP / UnitedStatesGAAP） |

---

## インデックス

| インデックス名 | カラム | 種別 |
|--------------|--------|------|
| PRIMARY | code | PRIMARY KEY |

---

## 備考
- サイクル1では `code = '6098'`（リクルートホールディングス）の1件のみを想定
- サイクル2で複数企業対応時にレコードが増える
