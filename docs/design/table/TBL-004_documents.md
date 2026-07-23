# TBL-004 documents（書類メタデータテーブル）

## 基本情報

| 項目 | 内容 |
|------|------|
| テーブルID | TBL-004 |
| テーブル名 | documents |
| 概要 | EDINETの書類一覧APIから取得した「どの書類が存在するか」の索引を保持する（サイクル9新設） |

サイクル8までの実装は、企業ごとに提出日を推測してEDINETの書類一覧APIを検索していたが、
このAPIは「日付を指定してその日の全提出書類を取得する」設計であり「企業を指定して
取得する」機能を持たない（`docs/external/edinet/EDINET_API_仕様書.pdf` 3-1-1参照）。
このAPIの設計に沿い、日付を指定して取得した書類一覧をそのまま保存しておくことで、
以降は書類本体の取得（書類取得API）を「どの書類を取ればよいか」が既知の状態から
開始できるようにする（`docs/requirements/cycle9_requirements.md` FR-48）。

`company_quantitative_facts`・`company_qualitative_facts`（値・テキストそのもの）
とは別テーブルで、まだ取り込んでいない書類も含めて保持する（`body_ingested_at`で
取り込み済みかを判定する）。

---

## カラム定義

| カラム名 | SQLAlchemy 型 | MySQL 型 | NOT NULL | PK | FK | 説明 |
|----------|--------------|----------|----------|----|-----|------|
| doc_id | String(8) | VARCHAR(8) | ✓ | ✓ | | EDINET書類管理番号（例：`S100YDHL`）。EDINET全体で一意なため、そのまま主キーにする |
| edinet_code | String(10) | VARCHAR(10) | ✓ | | | 提出者のEDINETコード |
| company_code | String(10) | VARCHAR(10) | ✓ | | companies.code | 証券コード（4桁）。書類一覧APIの`secCode`（5桁・末尾0）を`edinet_client.to_company_code`で変換した値。変換に失敗する書類・`companies`に存在しない企業の書類はそもそも保存しない |
| doc_type_code | String(3) | VARCHAR(3) | ✓ | | | 書類種別コード。`120`=有価証券報告書、`160`=半期報告書のみを保存対象とする |
| period_start | Date | DATE | | | | 対象期間（自）。書類一覧APIの`periodStart` |
| period_end | Date | DATE | | | | 対象期間（至）。書類一覧APIの`periodEnd` |
| submit_date_time | String(16) | VARCHAR(16) | ✓ | | | 提出日時（EDINETの`YYYY-MM-DD hh:mm`形式の文字列をそのまま保持） |
| list_date | Date | DATE | ✓ | | | この書類をどの日付の書類一覧取得で発見したか（書類一覧APIの`date`パラメータの値）。バックフィルの進捗管理に使う |
| withdrawal_status | String(1) | VARCHAR(1) | | | | 取下区分。`1`=取下書、`2`=取り下げられた書類、`0`=それ以外（`EDINET_API_仕様書.pdf` 3-1-2-2 No.32） |
| disclosure_status | String(1) | VARCHAR(1) | | | | 開示不開示区分 |
| csv_flag | String(1) | VARCHAR(1) | | | | CSV有無フラグ。`1`でない書類は書類取得APIでCSVを取得できないため、取り込み対象から除外する |
| body_ingested_at | DateTime | DATETIME | | | | この書類のCSVを取得し、企業の定量データ・定性データ（`company_quantitative_facts`・`company_qualitative_facts`）へ保存済みの日時。`NULL`＝未取得（旧名`facts_ingested_at`、サイクル13で命名是正） |

---

## インデックス

| インデックス名 | カラム | 種別 | 目的 |
|--------------|--------|------|------|
| PRIMARY | doc_id | PRIMARY KEY | |
| idx_documents_company_ingested | company_code, body_ingested_at | INDEX | 「この企業の未取得書類」を絞り込むクエリ（本体取り込みバッチ）を高速化 |
| idx_documents_list_date | list_date | INDEX | バックフィルの進捗確認（どの日付まで取り込み済みか）を高速化 |

---

## 外部キー制約

| 制約名 | カラム | 参照先 | ON DELETE |
|--------|--------|--------|-----------|
| fk_documents_company | company_code | companies.code | CASCADE |

---

## 備考

- **保存対象を絞り込む（YAGNI）**：EDINET全体では大量保有報告書・ファンドの書類等、
  本アプリが使わない書類も日々大量に提出されている。`secCode`を持たない書類・
  `doc_type_code`が`120`/`160`以外の書類は保存しない。これにより本テーブルの行数は
  「対象企業数×年数×書類種別数」程度に収まり、EDINET全体の提出件数に比例して
  無制限に膨らむことはない
- **`company_quantitative_facts`・`company_qualitative_facts`との関係**：
  `doc_id`は各テーブルに存在するが、外部キー関係は設けない（`documents`は
  「書類の存在」を表す索引、他の2テーブルは「値・テキストそのもの」を表す
  テーブルで、設計上の関心が異なるため。`company_qualitative_facts`のみ、
  1書類に対して行数が少ない〈最大3行〉ため例外的に外部キーを設けている）。
  将来、突合が必要になった場合はアプリケーション側で`doc_id`を使ってJOINする
- **`company_code`を`NOT NULL`にする理由**：変換に失敗した書類・`companies`に
  存在しない企業の書類は、そもそも本テーブルに保存しない設計にしている（サイクル9
  FR-49）。「保存されている＝正規に紐付けできた書類」という不変条件を保つことで、
  `company_code IS NULL`の考慮を本体取り込み処理に持ち込まずに済む
- **`submit_date_time`を`String`にする理由**：`date_format_policy.md`の方針に沿い、
  EDINETから返る文字列をそのまま保持する（アプリ側で日時型へのパース・タイムゾーン
  変換を行わない）。ソートや比較が必要になった場合は、その時点で型を見直す
