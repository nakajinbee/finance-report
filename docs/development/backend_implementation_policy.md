# バックエンド実装方針

`docs/design/cycle1_design.md`（技術スタック）を実装レベルまで具体化したメモ。
実装を始める前の技術選定の記録として残す。

---

## 言語・実行環境

| 項目 | 方針 | 理由 |
|---|---|---|
| Python | Homebrewの `python3.10` を使用 | システムの `python3` はXcode付属の3.9.6で更新非推奨のため使わない |
| 仮想環境 | `backend/.venv`（`python3.10 -m venv .venv`） | プロジェクトごとに依存を隔離 |
| パッケージ管理 | pip + `requirements.txt` | 標準ツールのみで完結。Poetry/uvは今回の依存数（数個）では過剰と判断し見送り |

---

## フレームワーク・ライブラリ構成

| レイヤー | 採用技術 | 備考 |
|---|---|---|
| Webフレームワーク | FastAPI | `docs/design/api/openapi.yaml` の設計と親和性が高い（自動ドキュメント生成） |
| ORM | SQLAlchemy 2.0系 | `docs/design/table/` のテーブル定義をそのままモデル化 |
| マイグレーション | Alembic（**手書きDDL方式**） | 最初から導入。`Base.metadata.create_all()`もautogenerateも使わず、`alembic revision`の空テンプレートに`op.execute("CREATE TABLE ...")`で生のDDLを直接書く。Flywayのバージョン管理されたSQLに近い運用。ORMモデル（`database.py`）とDDLは別物として手で同期を取る |
| DB | SQLite（開発時）→ MySQL（将来） | `DATABASE_URL`環境変数で接続先を切り替えるのみで移行できる構成にする |
| 環境変数管理 | `python-dotenv` + `backend/.env` | `.env`は`.gitignore`済み。`EDINET_API_KEY`・`DATABASE_URL`を格納 |
| EDINET通信 | 標準の`requests`（or `httpx`） | 追加のSDKは使わず、`memo/リクルートデータ取得メモ.md`の実機検証結果どおりに直接HTTPを叩く |

---

## ディレクトリ構成

`cycle1_design.md`の当初案（フラット構成）から、`docs/design/api/`のEDN/COMグルーピング
（`api_list.md`参照）にコード構造を合わせる形で具体化した。

```
backend/
├── main.py                # FastAPIインスタンス生成・ルーター登録のみ（薄く保つ）
├── routers/
│   ├── edinet.py            # API-EDN-001〜003（openapi.yaml paths/edinet/ に対応）
│   └── companies.py         # API-COM-001〜005（openapi.yaml paths/com/ に対応）
├── schemas.py               # Pydanticモデル（openapi.yaml components/schemas/ をそのまま型として定義）
├── edinet_client.py          # EDINET外部APIとの通信専用（memo/リクルートデータ取得メモ.md の①②API）
├── xbrl_parser.py            # CSVから要素ID・値を抜き出す汎用パーサー（TBL-003 facts向け、サイクル2で拡張）
├── metric_mappings.py         # 会計基準（J-GAAP/IFRS/US GAAP）ごとの要素IDマッピング・財務分析指標の計算式（サイクル3で追加）
├── database.py                # SQLAlchemyエンジン・セッション・ORMモデル（TBL-001 companies, TBL-003 facts。TBL-002 financialsはサイクル2で廃止済み）
├── alembic/                   # マイグレーション（alembic init で生成）
├── alembic.ini
├── requirements.txt
├── financials.db               # SQLite実体（.gitignore対象。ファイル名は初期のまま、中身はTBL-003 facts方式）
└── .env                        # 秘密情報（.gitignore対象）
```

`edinet.py`という名前は「EDINET外部APIとの通信モジュール」と「`routers/edinet.py`（社内APIルーティング）」で
紛らわしくなるため、外部通信側は`edinet_client.py`という名前にする。

---

## 実装の思想（アーキテクチャ原則）

1. **依存の向きは一方向**：`main.py` → `routers/` → (`edinet_client.py` / `xbrl_parser.py` / `database.py`)。
   逆方向の依存（例：`database.py`が`routers`を知っている）は作らない
2. **ルーターは薄く保つ**：`routers/`にはHTTPの入出力変換とエラーハンドリングだけを置き、
   EDINET通信・パース・DB操作のロジックは各専用モジュールに置く
3. **命名・型は設計書とトレーサブル**：関数名・変数名は`api_list.md`のAPI-ID、`openapi.yaml`のoperationId、
   `schemas.py`の型名と一致させ、「このコードがどの設計書の要素か」を名前だけで辿れるようにする
4. **エラーは例外で受け渡し、ルーターで変換**：`edinet_client.py`等はPython例外を投げるだけにし、
   `routers/`側で`openapi.yaml`の`Error`スキーマ（`{error, message}`）に変換してレスポンスを返す（FR-03対応）
5. **スコープ外の先取りをしない**：サイクル2（複数企業対応）を見越した抽象化（企業IDの汎用化等）は
   今回行わない。`cycle1_requirements.md`のスコープ外リストどおり、リクルートHD固定のコードでよい

---

## 実装順序

設計ドキュメントの依存関係に沿って、下から積み上げる。

1. **DB層**（`database.py` + Alembic）— テーブル定義を実装し、単体で作成・確認できる状態にする（完了）
2. **EDINETクライアント**（`edinet_client.py`）— `memo/リクルートデータ取得メモ.md`で確定した①②APIの叩き方を実装
3. **XBRLパーサー**（`xbrl_parser.py`）— 取得したCSVから5要素ID（`docs/requirements/cycle1_requirements.md` FR-01参照）を抽出しDBモデルにマッピング
4. **スキーマ層**（`schemas.py`）— `openapi.yaml`の`components/schemas/`をPydanticモデルとして定義
5. **API層**（`routers/edinet.py` / `routers/companies.py` / `main.py`）— `docs/design/api/openapi.yaml`どおりのエンドポイントを実装

各層は前段が動作確認できてから次に進む（DBが完成する前にAPI層を書き始めない）。

---

## コーディング方針

- 型ヒントを必須とする（FastAPI/SQLAlchemy 2.0はいずれも型ヒント前提の設計）
- 関数・クラス・変数の名前は、そのユースケースや機能が読んで分かる名前にする（`data`・`temp`・`process`のような汎用名は避け、`fetch_recruit_annual_reports`のように「何をするか」が伝わる名前にする）
- コメントは「WHY」のみ。関数名・変数名で意図が伝わるようにする
- カラム名・変数名は設計書（TBL-001/002、openapi.yamlのスキーマ）の命名にそのまま合わせる（変換の揺れを作らない）
- 日付・時刻の型とフォーマットは[date_format_policy.md](date_format_policy.md)に従う（`date`と`datetime`を混在させない、UTC変換をしない等）
- APIキーや接続文字列はコードにハードコードしない（`.env`経由のみ）
- EDINETからダウンロードしたZIP/CSVはディスクに書き出さず、メモリ上でパース→DB保存まで完結させる（`docs/design/cycle1_design.md`の「ダウンロードデータの取り扱い方針」参照。並行リクエストでのファイル名衝突を設計上起こさないための方針）
- テストフレームワーク（pytest等）は現時点では未導入。ロジックが複雑化した段階（パーサーの分岐が増える等）で改めて検討する。現状は`docs/development/self_review_rule.md`に沿った手動確認で担保する

---

## 未決事項（実装中に必要になったら決める）

- EDINETクライアントの同期/非同期（`requests` vs `httpx`＋`async def`）は`main.py`のダウンロードAPI（`API-EDN-001`）が非同期進行を要求するため、実装時に確定させる
- CORS設定（フロントエンドのdev serverオリジンを許可するか）はフロントエンドのビルドツール確定後に決める
