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
│   └── cycle1〜9_requirements.md / _review.md
│
├── design/                               ← 設計
│   ├── self_review_rule.md
│   ├── design_guideline.md               ← 本番デザインコンセプト（配色・タイポグラフィ等、常に最終断面のみ）
│   ├── cycle1,3,4,5,6,7,8,9_design.md / _review.md
│   ├── screen/                           ← 画面定義書（詳細：screen/screen_list.md）
│   ├── api/                              ← API設計書（詳細：api/api_list.md、openapi.yaml）
│   ├── table/                            ← テーブル定義書（詳細：table/table_list.md、er_diagram.md）
│   └── batch/                            ← バッチ定義書（詳細：batch/batch_list.md。新規バッチ追加時は必ずセットで更新）
│
├── development/                          ← 開発
│   ├── self_review_rule.md
│   ├── cycle2〜11_development_review.md
│   ├── cycle7_batch_timing_estimate.md   ← 全社展開時の所要時間・データ量見積もり＋サイクル8の再検証結果（旧方式、IDEA-01フェーズ2）
│   ├── cycle10_db_migration_decision.md  ← SQLite継続／他DB移行の判断（IDEA-01フェーズ6）
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
│   └── IDEA-01〜14
│
├── product/                              ← プロダクトコンセプト
│   └── concept.md                        ← 想定利用者・提供価値・事業化スタンス（常に最終断面のみ）
│
└── external/edinet/                      ← EDINET公式仕様書（PDF）
```

`.claude/skills/`（プロジェクトルート）には、進め方を型化したSkillsがある：
`cycle-workflow`・`design-apply`・`todo-tracker`・`req-design-traceability`。

大きな負荷がかかる操作（外部APIへの大量アクセス等）・データの更新削除・
アーキテクチャ変更は、実行前にユーザーへ明示的に確認する（cycle-workflow参照）。

---

## 現在のフェーズ

| サイクル | 内容 | 状態 |
|---|---|---|
| サイクル1 | 基本機能（EDINET連携・DB保存・3画面） | 完了 |
| サイクル2 | 企業検索・期間指定・汎用ファクトテーブル・SCR-004追加 | 完了 |
| サイクル3 | 財務分析指標（ROE等12指標）の追加 | 完了 |
| サイクル4 | 共通ヘッダー・フッター、仮のデザイン整理 | 完了 |
| サイクル5 | 本番デザインコンセプト策定・実装（design_guideline.md） | 完了 |
| サイクル6 | 全上場企業マスタの一括登録（[IDEA-01](ideas/IDEA-01_db_batch_ingestion.md)フェーズ1） | 完了 |
| サイクル7 | バッチ取得の技術検証（[IDEA-01](ideas/IDEA-01_db_batch_ingestion.md)フェーズ2） | 完了 |
| サイクル8 | 書類一覧APIの日付単位キャッシュ導入・再検証（[IDEA-01](ideas/IDEA-01_db_batch_ingestion.md)フェーズ3準備） | 完了 |
| サイクル9 | 書類一覧・書類本体の取り込み処理を日付ポーリング方式で実装（[IDEA-01](ideas/IDEA-01_db_batch_ingestion.md)フェーズ3・4） | 完了 |
| サイクル10 | データ量・並行アクセスパターンをもとにDB移行判断（[IDEA-01](ideas/IDEA-01_db_batch_ingestion.md)フェーズ6） | 完了 |
| サイクル11 | アプリのビジネスコンセプト決定（[IDEA-14](ideas/IDEA-14_business_concept_definition.md)、[product/concept.md](product/concept.md)） | 完了 |
| サイクル12 | ユースケース設計（[IDEA-13](ideas/IDEA-13_use_case_design.md)） | 企画待ち |

現時点で残っている大きな論点：
- アプリのコンセプトはサイクル11で決定済み（[product/concept.md](product/concept.md)）。
  これを前提にサイクル12でユースケース設計（[IDEA-13](ideas/IDEA-13_use_case_design.md)）
  に進む。[IDEA-10](ideas/IDEA-10_report_purpose_redesign.md)（レポート表示の再設計）は
  ユースケース設計の後
- サイクル9でBATCH-003（書類一覧バックフィル、過去10年分・41,567件を実行済み）・
  BATCH-004（書類本体取り込み、30件サンプルで動作確認済み）を実装した。
  BATCH-004の全社・全件規模での本実行、日次実行の自動化（IDEA-01フェーズ4の完成）は
  次サイクル以降（詳細：[batch/batch_list.md](design/batch/batch_list.md)、
  backlog：[requirements/cycleX_backlog.md](requirements/cycleX_backlog.md)）
- IDEA-01は全6フェーズが完了した（フェーズ6の判断：SQLite継続。詳細：
  [development/cycle10_db_migration_decision.md](development/cycle10_db_migration_decision.md)）。
  残るのはフェーズ3・4の「全社規模の本実行・自動化」のみ（上記backlog参照）

---

## クイックリンク

| 知りたいこと | 参照先 |
|---|---|
| 画面一覧 | [design/screen/screen_list.md](design/screen/screen_list.md) |
| テーブル一覧 | [design/table/table_list.md](design/table/table_list.md) |
| テーブルの関係（ER図） | [design/table/er_diagram.md](design/table/er_diagram.md) |
| APIエンドポイント一覧 | [design/api/api_list.md](design/api/api_list.md) |
| バッチ処理一覧 | [design/batch/batch_list.md](design/batch/batch_list.md) |
| デザインのルール（色・フォント・状態表現等） | [design/design_guideline.md](design/design_guideline.md) |
| アプリのコンセプト（想定利用者・提供価値・事業化スタンス） | [product/concept.md](product/concept.md) |
| まだ検討中のアイデア | [ideas/README.md](ideas/README.md) |
| 「やる」と決まったが未着手の事項 | [requirements/cycleX_backlog.md](requirements/cycleX_backlog.md) |
| 会計・EDINETのドメイン知識 | [domain/](domain/) |
| 日付表記のルール | [development/date_format_policy.md](development/date_format_policy.md) |
