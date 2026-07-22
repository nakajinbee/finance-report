# ドキュメント INDEX

プロジェクト全体のドキュメント構成。Claude がコンテキストを把握するための参照ファイル。
**このファイルには詳細を書かない。一覧・詳細は各セクションの「詳細」リンク先を見る**
（詳細をここに書き写すと二重管理になり、更新漏れで陳腐化する。実際に過去そうなった）。

毎サイクル終了時（実装セルフレビュー完了後、コミット前）に、このファイルの
「ディレクトリ構成」「現在のフェーズ」を最新化すること（[cycle-workflow Skill](../.claude/skills/cycle-workflow/SKILL.md)参照）。

---

## ディレクトリ構成

```
docs/
├── INDEX.md                              ← このファイル
├── self_review_guidelines.md             ← セルフレビュー全体概要
│
├── requirements/                         ← 要件定義（cycleN_requirements.md・レビュー結果）
│   ├── self_review_rule.md
│   ├── cycleX_backlog.md                 ← 「やる」と決まったが未着手の事項（一元管理）
│   └── cycle1〜5_requirements.md / _review.md
│
├── design/                               ← 設計
│   ├── self_review_rule.md
│   ├── design_guideline.md               ← 本番デザインコンセプト（配色・タイポグラフィ等、常に最終断面のみ）
│   ├── cycle1,3,4,5_design.md / _review.md
│   ├── screen/                           ← 画面定義書（詳細：screen/screen_list.md）
│   ├── api/                              ← API設計書（詳細：api/api_list.md、openapi.yaml）
│   └── table/                            ← テーブル定義書（詳細：table/table_list.md）
│
├── development/                          ← 開発
│   ├── self_review_rule.md
│   ├── cycle2〜5_development_review.md
│   ├── backend_implementation_policy.md
│   ├── frontend_implementation_policy.md
│   ├── date_format_policy.md             ← fiscal_year等の日付表記ルール（重要：動的再生成禁止）
│   └── repository_management_policy.md
│
├── domain/                               ← ドメイン知識
│   ├── accounting_standards.md           ← 会計基準（J-GAAP / IFRS / US GAAP）の違い
│   ├── xbrl_tagging_variability.md       ← EDINET XBRLタグの企業・基準ごとの揺れ
│   └── 会計基準/会計基準の基礎知識.md
│
├── ideas/                                ← 検討段階のアイデア（詳細：ideas/README.md）
│   └── IDEA-01〜13
│
└── external/edinet/                      ← EDINET公式仕様書（PDF）
```

`.claude/skills/`（プロジェクトルート）には、進め方を型化したSkillsがある：
`cycle-workflow`・`design-apply`・`todo-tracker`・`req-design-traceability`。

---

## 現在のフェーズ

| サイクル | 内容 | 状態 |
|---|---|---|
| サイクル1 | 基本機能（EDINET連携・DB保存・3画面） | 完了 |
| サイクル2 | 企業検索・期間指定・汎用ファクトテーブル・SCR-004追加 | 完了 |
| サイクル3 | 財務分析指標（ROE等12指標）の追加 | 完了 |
| サイクル4 | 共通ヘッダー・フッター、仮のデザイン整理 | 完了 |
| サイクル5 | 本番デザインコンセプト策定・実装（design_guideline.md） | 完了 |
| 次サイクル | 未定。[ideas/README.md](ideas/README.md)・[requirements/cycleX_backlog.md](requirements/cycleX_backlog.md)から検討 | 企画待ち |

現時点で残っている大きな論点：アプリのコンセプト・想定利用者が未決定
（[ideas/IDEA-10](ideas/IDEA-10_report_purpose_redesign.md)・[IDEA-13](ideas/IDEA-13_use_case_design.md)がこれ待ち）。

---

## クイックリンク

| 知りたいこと | 参照先 |
|---|---|
| 画面一覧 | [design/screen/screen_list.md](design/screen/screen_list.md) |
| テーブル一覧 | [design/table/table_list.md](design/table/table_list.md) |
| APIエンドポイント一覧 | [design/api/api_list.md](design/api/api_list.md) |
| デザインのルール（色・フォント・状態表現等） | [design/design_guideline.md](design/design_guideline.md) |
| まだ検討中のアイデア | [ideas/README.md](ideas/README.md) |
| 「やる」と決まったが未着手の事項 | [requirements/cycleX_backlog.md](requirements/cycleX_backlog.md) |
| 会計・EDINETのドメイン知識 | [domain/](domain/) |
| 日付表記のルール | [development/date_format_policy.md](development/date_format_policy.md) |
