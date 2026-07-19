# ドキュメント INDEX

プロジェクト全体のドキュメント構成。Claude がコンテキストを把握するための参照ファイル。

---

## ディレクトリ構成

```
docs/
├── INDEX.md                              ← このファイル
├── self_review_guidelines.md             ← セルフレビュー全体概要
│
├── requirements/                         ← 要件定義
│   ├── self_review_rule.md               ← 要件定義フェーズのレビュールール
│   ├── cycle1_requirements.md            ← サイクル1 要件定義（現行）
│   └── cycle1_requirements_review.md    ← サイクル1 要件定義セルフレビュー結果
│
├── design/                               ← 設計
│   ├── self_review_rule.md               ← 設計フェーズのレビュールール
│   ├── cycle1_design.md                  ← サイクル1 設計概要（技術スタック・アーキテクチャ・DB・ディレクトリ構成）
│   │
│   ├── screen/                           ← 画面定義書
│   │   ├── screen_list.md                ← 画面一覧（画面ID・画面名・概要）
│   │   ├── SCR-001_download.md           ← ダウンロード画面
│   │   ├── SCR-002_company_list.md       ← 企業一覧画面
│   │   └── SCR-003_company_detail.md     ← 企業詳細画面
│   │
│   ├── api/                              ← API 設計書
│   │   └── openapi.yaml                  ← OpenAPI 3.0 定義（全4エンドポイント）
│   │
│   └── table/                            ← テーブル定義書
│       ├── table_list.md                 ← テーブル一覧
│       ├── TBL-001_companies.md          ← companies テーブル定義
│       └── TBL-002_financials.md         ← financials テーブル定義
│
├── development/                          ← 開発
│   └── self_review_rule.md               ← 開発フェーズのレビュールール
│
├── domain/                               ← ドメイン知識
│   └── accounting_standards.md           ← 会計基準（J-GAAP / IFRS / US GAAP）の違いと設計考慮事項
│
└── external/                             ← 外部連携
    └── edinet/                           ← EDINET 関連
        ├── EDINET_API_仕様書.pdf          ← EDINET API 公式仕様書
        ├── XBRL_フレームワーク設計書.pdf  ← XBRL フレームワーク設計書
        └── XBRL_フレームワーク設計書_別紙.pdf
```

---

## API エンドポイント一覧（openapi.yaml より）

| メソッド | パス | 概要 |
|----------|------|------|
| POST | `/api/download` | EDINET からデータ取得・DB 保存開始 |
| GET | `/api/download/status` | ダウンロード進捗確認（ポーリング用） |
| GET | `/api/companies` | DB 保存済み企業一覧取得 |
| GET | `/api/companies/{code}/financials` | 指定企業の財務データ取得（全指標・全期分） |

---

## 画面一覧（screen_list.md より）

| 画面ID | 画面名 | パス | 概要 |
|--------|--------|------|------|
| SCR-001 | ダウンロード画面 | `/download` | EDINET からデータ取得・DB 保存 |
| SCR-002 | 企業一覧画面 | `/companies` | 保存済み企業を検索・一覧表示 |
| SCR-003 | 企業詳細画面 | `/companies/:code` | 選択企業の財務グラフ表示 |

---

## テーブル一覧（table_list.md より）

| テーブルID | テーブル名 | 概要 |
|-----------|-----------|------|
| TBL-001 | companies | 企業マスタ（企業名・証券コード・業種・会計基準） |
| TBL-002 | financials | 財務データ（期別の売上高・営業利益・純利益・総資産・負債合計） |

---

## 現在のフェーズ

| フェーズ | 状態 |
|----------|------|
| サイクル1 要件定義 | 完了（レビュー済み） |
| サイクル1 設計 | 進行中 |
| サイクル1 開発 | 未着手 |
| サイクル1 テスト | 未着手 |
