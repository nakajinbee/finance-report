# サイクル1 設計書

## 技術スタック

| レイヤー | 採用技術 |
|----------|----------|
| フロントエンド | React + TypeScript |
| ルーティング | React Router v6 |
| グラフ描画 | Recharts |
| バックエンド | Python / FastAPI |
| データ永続化 | SQLite（`financials.db`）※将来 MySQL へ移行予定 |
| ORM | SQLAlchemy（DB 移行を容易にするため） |
| XBRL パース | EDINET の財務サマリー CSV を使用（arelle より軽量） |
| 通信 | REST API（JSON） |
| APIキー管理 | サーバーサイド環境変数（`.env`） |

---

## アーキテクチャ

```
[ブラウザ]
    ↓ HTTP
[FastAPI サーバー]
    ├─ EDINET API（書類一覧・CSV ダウンロード）
    └─ SQLite DB（取得済みデータの保存・参照）
```

---

## ダウンロードデータの取り扱い方針

EDINETからダウンロードした書類（ZIP・CSV）は、**ディスクに保存せず、メモリ上でのみ扱い、
DBへの保存が終わったら破棄する**。

```
EDINET書類取得API
    ↓ ZIPのバイト列（メモリ上）
zipfile.ZipFile で展開（メモリ上、一時ファイルなし）
    ↓ CSVのバイト列（メモリ上）
xbrl_parser.py でパース（メモリ上）
    ↓ 5指標の数値
database.py で financials テーブルにINSERT
    （ここでメモリ上のZIP/CSVは破棄される）
```

**理由**
- ダウンロードしたファイルを`backend/`配下の共通パスに書き出す設計にすると、
  複数のダウンロードリクエストが同時に走った場合にファイル名の衝突・書き込み中の
  読み込みといった競合が発生しうる。ファイルを永続化せずメモリ上で完結させることで、
  この種の競合が原理的に発生しない
- サイクル1の要件（`docs/requirements/cycle1_requirements.md`）に、ダウンロードした
  生データ（ZIP/XBRL/CSV）自体を保管・再利用する要件はない。DBに保存する5指標さえ
  抽出できればよく、生ファイルを残す必要がない
- `SCR-001`（ダウンロード画面）の仕様上、ダウンロード処理はそもそも多重実行を防止する
  設計になっている（`docs/design/api/paths/edinet/download.yaml`の`409`レスポンス）ため、
  同一プロセス内で同じ書類を同時に2回ダウンロードする状況自体が起こらない

**実装との対応**：`backend/edinet_client.py`の`fetch_annual_report_csv()`は
`io.BytesIO`でZIPをメモリ展開し、CSVのバイト列を戻り値として返すのみで、
ファイルシステムへの書き込みを一切行わない。

---

## 画面構成

3画面を React Router で管理する。

| パス | 画面名 | 役割 |
|------|--------|------|
| `/download` | ダウンロード画面 | EDINET からデータ取得・DB 保存 |
| `/companies` | 企業一覧画面 | DB 保存済みの企業を一覧表示 |
| `/companies/:code` | 企業詳細画面 | 選択企業の財務グラフ表示 |

---

## 画面設計

### 1. ダウンロード画面 `/download`

```
┌────────────────────────────────────┐
│  データ取得                          │
│                                    │
│  対象企業：リクルートホールディングス  │
│  取得期間：直近5期分                  │
│                                    │
│        [ データを取得する ]           │
│                                    │
│  ─────────────────────────         │
│  取得ログ：                          │
│  ✓ 2023年3月期 取得完了             │
│  ✓ 2022年3月期 取得完了             │
│  ⏳ 2021年3月期 取得中...            │
└────────────────────────────────────┘
```

- ボタン押下で EDINET API を叩いてデータ取得・DB 保存を開始
- 取得進捗をログ形式でリアルタイム表示（ポーリングまたは SSE）
- 取得完了後「企業一覧へ」ボタンを表示

### 2. 企業一覧画面 `/companies`

```
┌────────────────────────────────────┐
│  企業一覧                            │
│                                    │
│  ┌──────────────────────────────┐  │
│  │ リクルートホールディングス      │  │
│  │ 証券コード：6098　IFRS         │  │
│  │ データ期間：2019年3月期〜       │  │
│  │ 2023年3月期（5期分）           │  │
│  └──────────────────────────────┘  │
│                                    │
│        [ データを追加取得する ]       │
└────────────────────────────────────┘
```

- DB に保存済みの企業カードを一覧表示
- カードクリックで企業詳細画面へ遷移
- 「データを追加取得する」でダウンロード画面へ戻る

### 3. 企業詳細画面 `/companies/:code`

```
┌────────────────────────────────────┐
│  リクルートホールディングス            │
│  会計基準：IFRS  対象期間：5期分       │
├────────────────────────────────────┤
│  [売上高] [営業利益] [純利益]          │
│  [総資産] [負債合計]                   │
├────────────────────────────────────┤
│                                    │
│   ███                              │
│   ███  ███                         │
│   ███  ███  ███                    │
│   ███  ███  ███  ███               │
│   ███  ███  ███  ███  ███          │
│  ──────────────────────────        │
│  FY19  FY20  FY21  FY22  FY23     │
│                                    │
│  直近値：3兆2,798億円                │
└────────────────────────────────────┘
```

- 指標ボタンで表示する指標を切り替え（1画面に1指標）
- 棒グラフ + 直近値テキスト
- 単位：億円

### 画面の状態管理

| 状態 | 表示 |
|------|------|
| ローディング | スピナー＋「データを取得しています...」 |
| 正常 | グラフ＋直近値 |
| APIエラー | 「データの取得に失敗しました。しばらくしてから再度お試しください。」 |
| データなし | 「データなし」 |

---

## 内部 API 設計

### POST `/api/download`
EDINET からリクルートの財務データを取得して DB に保存する。

**レスポンス（SSE or ポーリング用）**
```json
{ "status": "in_progress", "message": "2023年3月期 取得完了" }
{ "status": "done", "message": "5期分の取得が完了しました" }
{ "status": "error", "message": "データの取得に失敗しました" }
```

### GET `/api/companies`
DB に保存済みの企業一覧を返す。

```json
[
  {
    "code": "6098",
    "name": "リクルートホールディングス",
    "accounting_standard": "IFRS",
    "periods": ["2019-03-31", "2020-03-31", "2021-03-31", "2022-03-31", "2023-03-31"]
  }
]
```

### GET `/api/companies/{code}/financials`
指定企業の財務データを全期分返す。

```json
{
  "company": { "code": "6098", "name": "リクルートホールディングス", "accounting_standard": "IFRS" },
  "data": [
    {
      "fiscal_year": "2023年3月期",
      "period_end": "2023-03-31",
      "revenue": 3279800000000,
      "operating_profit": 412300000000,
      "net_profit": 296100000000,
      "total_assets": 2987600000000,
      "total_liabilities": 1543200000000
    }
  ]
}
```

---

## DB 設計

### 現在：SQLite　／　将来移行先：MySQL

SQLAlchemy ORM を使うことで、`DATABASE_URL` の環境変数を変えるだけで移行できる。

```
# SQLite（現在）
DATABASE_URL=sqlite:///./financials.db

# MySQL（移行後）
DATABASE_URL=mysql+pymysql://user:password@localhost:3306/financials
```

SQLite → MySQL 移行時の注意点：
- `TEXT` 型は MySQL では `VARCHAR(255)` 等に変更が必要（SQLAlchemy の型定義で吸収）
- `INTEGER` の自動採番は `AUTOINCREMENT` → `AUTO_INCREMENT`（SQLAlchemy が自動対応）
- MySQL サーバーの起動・DB・ユーザー作成が別途必要

### `companies` テーブル
| カラム | 型 | 説明 |
|--------|----|------|
| code | String(10) PK | 証券コード |
| name | String(255) | 企業名 |
| accounting_standard | String(50) | 会計基準（IFRS等） |

### `financials` テーブル
| カラム | 型 | 説明 |
|--------|----|------|
| id | Integer PK AutoIncrement | |
| company_code | String(10) FK | 証券コード |
| period_end | Date | 会計期間終了日 |
| fiscal_year | String(20) | 表示用（例：2023年3月期） |
| revenue | BigInteger | 売上高（円） |
| operating_profit | BigInteger | 営業利益（円） |
| net_profit | BigInteger | 純利益（円） |
| total_assets | BigInteger | 総資産（円） |
| total_liabilities | BigInteger | 負債合計（円） |

※ 型は SQLAlchemy の型名で記載。整数型は `INTEGER` でなく `BigInteger` を使用（兆円規模に対応）。

---

## ディレクトリ構成

```
project/
├── backend/
│   ├── main.py           # FastAPI エントリポイント・ルーティング
│   ├── edinet.py         # EDINET API クライアント
│   ├── xbrl_parser.py    # CSV パース・指標抽出
│   ├── database.py       # SQLite 操作
│   ├── financials.db     # SQLite DB（git 管理外）
│   └── .env              # APIキー（git 管理外）
└── frontend/
    ├── src/
    │   ├── App.tsx                          # Router 設定
    │   ├── pages/
    │   │   ├── DownloadPage.tsx             # ダウンロード画面
    │   │   ├── CompanyListPage.tsx          # 企業一覧画面
    │   │   └── CompanyDetailPage.tsx        # 企業詳細画面
    │   ├── components/
    │   │   ├── FinancialChart.tsx           # グラフ
    │   │   ├── MetricSelector.tsx           # 指標切り替えボタン
    │   │   └── ErrorMessage.tsx             # エラー表示
    │   └── api/
    │       └── client.ts                    # バックエンド API 呼び出し
    └── package.json
```
