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
| 1 | API-EDN-001 | POST | `/api/download` | EDINET から財務データを取得しDBに保存する（非同期開始） | `paths/edinet/download.yaml` |
| 2 | API-EDN-002 | GET | `/api/download/status` | API-EDN-001 の進捗状況を返す | `paths/edinet/download_status.yaml` |

---

## API-COM（企業データ参照系）

| No | APIID | Method | Path | 概要 | ファイル |
|----|-------|--------|------|------|----------|
| 1 | API-COM-001 | GET | `/api/companies` | DBに保存済みの企業一覧を返す | `paths/com/companies.yaml` |
| 2 | API-COM-002 | GET | `/api/companies/{code}/financials` | 指定企業の財務データを全期分返す | `paths/com/companies_code_financials.yaml` |

---

## 画面とAPIの対応

| 画面ID | 画面名 | 使用API |
|---|---|---|
| SCR-001 | ダウンロード画面 | API-EDN-001, API-EDN-002 |
| SCR-002 | 企業一覧画面 | API-COM-001 |
| SCR-003 | 企業詳細画面 | API-COM-002 |
