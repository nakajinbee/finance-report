# API一覧

内部API（バックエンド `/api/*`）のID一覧。EDINET APIそのものではなく、
このアプリのFastAPIが提供するエンドポイントを対象とする。

IDは2グループに分ける。

| プレフィックス | 意味 | 格納先 |
|---|---|---|
| `API-EDN-xxx` | EDINETにアクセスする系のAPI（外部APIを呼び出す） | `paths/edinet/` |
| `API-COM-xxx` | 企業（Company）データをDBから参照・更新する系のAPI（EDINETは呼ばない） | `paths/com/` |

---

## API-EDN（EDINETアクセス系）

| No | APIID | Method | Path | 概要 | ファイル |
|----|-------|--------|------|------|----------|
| 1 | API-EDN-001 | POST | `/api/download` | 指定企業・期間の財務データ（定量・定性）を取得しDBに保存する（非同期開始、サイクル2でcompany_code/period指定に対応、サイクル13でdocuments連携・定性データ保存を追加） | `paths/edinet/download.yaml` |
| 2 | API-EDN-002 | GET | `/api/download/status?company_code=` | API-EDN-001 の進捗状況を返す（サイクル2で企業単位に変更） | `paths/edinet/download_status.yaml` |
| 3 | API-EDN-003 | GET | `/api/edinet/companies/search?q=` | EDINETコードリストから企業名・証券コードで検索する（サイクル2新規、FR-07） | `paths/edinet/search.yaml` |

---

## API-COM（企業データ参照系）

| No | APIID | Method | Path | 概要 | ファイル |
|----|-------|--------|------|------|----------|
| 1 | API-COM-001 | GET | `/api/companies` | DBに保存済みの企業一覧を返す | `paths/com/companies.yaml` |
| 2 | API-COM-002 | GET | `/api/companies/{code}/financials?from_year=&to_year=` | 指定企業の財務データ（7指標）を返す（サイクル2で年度範囲指定に対応、FR-12） | `paths/com/companies_code_financials.yaml` |
| 3 | API-COM-003 | GET | `/api/companies/{code}/cashflow?from_year=&to_year=` | 指定企業のキャッシュフロー（3項目）を返す（サイクル2新規、FR-13） | `paths/com/companies_code_cashflow.yaml` |
| 4 | API-COM-005 | GET | `/api/companies/{code}/ratios?from_year=&to_year=` | 指定企業の財務分析指標（ROE・流動比率等）を返す（サイクル3新規、FR-23〜26） | `paths/com/companies_code_ratios.yaml` |
| 5 | API-COM-006 | GET | `/api/companies/{code}/qualitative-facts?period_end=` | 指定企業の定性データ（事業の内容・事業等のリスク・MD&A）を返す（サイクル13新規、FR-58） | `paths/com/companies_code_qualitative_facts.yaml` |

廃止：API-COM-004（`GET /api/companies/{code}/facts`、旧SCR-004向け）はサイクル13で
SCR-004削除に伴い削除した。

---

## 画面とAPIの対応

| 画面ID | 画面名 | 使用API |
|---|---|---|
| SCR-001 | ダウンロード画面 | API-EDN-001, API-EDN-002, API-EDN-003 |
| SCR-002 | 企業一覧画面 | API-COM-001 |
| SCR-003 | 企業詳細画面 | API-COM-002, API-COM-003, API-COM-005, API-COM-006 |
