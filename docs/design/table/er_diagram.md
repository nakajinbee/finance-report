# ER図（テーブル関係図）

対象：`docs/design/table/table_list.md`のテーブル一覧に対応する実際のER図。
現行テーブルは3つ（`TBL-002 financials`はサイクル2で廃止済み、`TBL-003 facts`に
置き換わっている）。

```mermaid
erDiagram
    companies ||--o{ facts : "1社が複数のfactsを持つ"
    companies ||--o{ documents : "1社が複数のdocumentsを持つ"

    companies {
        varchar(10) code PK "証券コード(4桁)"
        varchar(255) name "企業名"
        varchar(100) sector "業種(NULL可)"
        varchar(50) accounting_standard "会計基準。財務データ未取得ならNULL"
    }

    facts {
        int id PK
        varchar(10) company_code FK "companies.codeを参照"
        varchar(8) doc_id "EDINET書類ID"
        varchar(3) doc_type_code "書類種別(有報/半期報告書)"
        date period_end "会計期間終了日"
        varchar(255) element_id "XBRL要素ID"
        varchar(255) element_name "要素名(NULL可)"
        varchar(100) context_id "連結/個別・期間等の文脈ID"
        varchar(20) consolidated_or_individual "連結/個別(NULL可)"
        varchar(10) period_or_instant "期間/時点(NULL可)"
        varchar(20) unit "単位(NULL可)"
        numeric_30_4 value "数値"
    }

    documents {
        varchar(8) doc_id PK "EDINET書類管理番号"
        varchar(10) edinet_code "提出者のEDINETコード"
        varchar(10) company_code FK "companies.codeを参照"
        varchar(3) doc_type_code "書類種別(有報/半期報告書のみ保存)"
        date period_start "対象期間(自)(NULL可)"
        date period_end "対象期間(至)(NULL可)"
        varchar(16) submit_date_time "提出日時(文字列のまま保持)"
        date list_date "書類一覧取得時のdateパラメータ値"
        varchar(1) withdrawal_status "取下区分(NULL可)"
        varchar(1) disclosure_status "開示不開示区分(NULL可)"
        varchar(1) csv_flag "CSV有無フラグ(NULL可)"
        datetime facts_ingested_at "facts取り込み済み日時(NULL=未取得)"
    }
```

## 読み方

- `companies`（TBL-001）：企業マスタ。1行＝1企業
- `facts`（TBL-003）：EDINETから取得した数値データを、勘定科目（要素ID）単位で
  1行ずつ保持する汎用テーブル。1企業に対して大量の行がぶら下がる
  （例：33社で約31万行、1社平均約9,400行）
- `documents`（TBL-004、サイクル9新設）：EDINETの書類一覧APIで発見した「書類の存在」を
  保持する索引テーブル。`facts`とは別系統で、`facts`へまだ取り込んでいない書類も含む
  （`facts_ingested_at`が`NULL`のものが未取込）
- `companies`から見て`facts`・`documents`はどちらも1対多。`facts`と`documents`の間には
  直接の外部キー関係を持たない（`doc_id`は両方に存在するが、参照制約は設けていない。
  両者は「値そのもの」と「書類の存在」という異なる関心事を表すため）。企業を削除すると
  紐づく`facts`・`documents`も連動して消える（`ON DELETE CASCADE`）
- `facts`は「売上高」「純利益」のような個別カラムを持たない。同じテーブルの中に
  あらゆる勘定科目が`element_id`で区別されて並んでおり、画面表示用の
  「売上高」「ROE」等の指標は、アプリ側（`backend/metric_mappings.py`等）が
  `element_id`ごとの値を都度組み立てて計算している
- `companies.accounting_standard`が`NULL`の企業は、基本情報のみ登録済みで
  財務データ（＝紐づく`facts`行）がまだ0件の企業（サイクル6 FR-39・FR-40）

## 一意制約・インデックス

| テーブル | 種類 | 対象カラム | 目的 |
|---|---|---|---|
| facts | UNIQUE | company_code, doc_id, element_id, context_id | 同じ書類・同じ要素・同じ文脈の重複行を防ぐ |
| facts | INDEX | company_code, element_id | 指標計算時の絞り込みを高速化 |
| facts | INDEX | company_code, period_end | 年度範囲指定（FR-12）でのクエリを高速化 |
| documents | INDEX | company_code, facts_ingested_at | 「この企業の未取得書類」の絞り込みを高速化 |
| documents | INDEX | list_date | バックフィルの進捗確認を高速化 |

## 廃止済みテーブル（参考）

`TBL-002 financials`（サイクル1で導入、サイクル2で廃止）は、勘定科目ごとに固定カラムを
持つ設計（`revenue`・`operating_profit`等）だった。新しい勘定科目が増えるたびにカラムを
追加する必要があり拡張性が低いため、汎用的な`facts`テーブルに置き換えられた
（詳細：[TBL-003_facts.md](TBL-003_facts.md)）。

## 各テーブルの詳細定義

- [TBL-001_companies.md](TBL-001_companies.md)
- [TBL-003_facts.md](TBL-003_facts.md)
- [TBL-004_documents.md](TBL-004_documents.md)
