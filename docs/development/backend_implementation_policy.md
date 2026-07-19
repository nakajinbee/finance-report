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

## ディレクトリ構成（`cycle1_design.md`準拠）

```
backend/
├── main.py           # FastAPIエントリポイント・ルーティング（openapi.yamlのAPI-*を実装）
├── edinet.py          # EDINET APIクライアント（書類一覧API／書類取得API）
├── xbrl_parser.py      # CSVから要素IDを抜き出すパーサー
├── database.py         # SQLAlchemyエンジン・セッション・ORMモデル（TBL-001/002）
├── alembic/            # マイグレーション（alembic init で生成）
├── alembic.ini
├── requirements.txt
├── financials.db        # SQLite実体（.gitignore対象）
└── .env                 # 秘密情報（.gitignore対象）
```

---

## 実装順序

設計ドキュメントの依存関係に沿って、下から積み上げる。

1. **DB層**（`database.py` + Alembic）— テーブル定義を実装し、単体で作成・確認できる状態にする
2. **EDINETクライアント**（`edinet.py`）— `memo/リクルートデータ取得メモ.md`で確定した①②APIの叩き方を実装
3. **XBRLパーサー**（`xbrl_parser.py`）— 取得したCSVから5要素ID（`docs/requirements/cycle1_requirements.md` FR-01参照）を抽出しDBモデルにマッピング
4. **API層**（`main.py`）— `docs/design/api/openapi.yaml`・`paths/edinet/`・`paths/com/`どおりのエンドポイントを実装

各層は前段が動作確認できてから次に進む（DBが完成する前にAPI層を書き始めない）。

---

## コーディング方針

- 型ヒントを必須とする（FastAPI/SQLAlchemy 2.0はいずれも型ヒント前提の設計）
- コメントは「WHY」のみ。関数名・変数名で意図が伝わるようにする
- カラム名・変数名は設計書（TBL-001/002、openapi.yamlのスキーマ）の命名にそのまま合わせる（変換の揺れを作らない）
- APIキーや接続文字列はコードにハードコードしない（`.env`経由のみ）
- テストフレームワーク（pytest等）は現時点では未導入。ロジックが複雑化した段階（パーサーの分岐が増える等）で改めて検討する。現状は`docs/development/self_review_rule.md`に沿った手動確認で担保する

---

## 未決事項（実装中に必要になったら決める）

- EDINETクライアントの同期/非同期（`requests` vs `httpx`＋`async def`）は`main.py`のダウンロードAPI（`API-EDN-001`）が非同期進行を要求するため、実装時に確定させる
- CORS設定（フロントエンドのdev serverオリジンを許可するか）はフロントエンドのビルドツール確定後に決める
