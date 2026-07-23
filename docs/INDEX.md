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
│   └── cycle1〜13_requirements.md / _review.md
│
├── design/                               ← 設計
│   ├── self_review_rule.md
│   ├── design_guideline.md               ← 本番デザインコンセプト（配色・タイポグラフィ等、常に最終断面のみ）
│   │   （cycleN_design.mdはサイクル13で廃止・過去分も削除済み。設計の成果物は
│   │   画面/API/テーブル/バッチの定義書を直接更新する形に統一した。設計セルフ
│   │   レビューの記録＝cycleN_design_review.mdは今後も作成する）
│   ├── screen/                           ← 画面定義書（詳細：screen/screen_list.md）
│   ├── api/                              ← API設計書（詳細：api/api_list.md、openapi.yaml）
│   ├── table/                            ← テーブル定義書（詳細：table/table_list.md、er_diagram.md）
│   └── batch/                            ← バッチ定義書（詳細：batch/batch_list.md。新規バッチ追加時は必ずセットで更新）
│
├── development/                          ← 開発
│   ├── self_review_rule.md
│   ├── cycle2〜13_development_review.md
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
│   ├── concept.md                        ← 想定利用者・提供価値・事業化スタンス（常に最終断面のみ）
│   ├── use_cases.md                      ← ユースケース一覧（大項目/中項目/小項目、UC-x-xで参照。常に最終断面のみ）
│   └── use_case_details/                 ← ユースケース詳細（画面遷移・関連機能・依存関係。大項目ごとにフォルダ分け）
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
| サイクル12 | ユースケース設計（[IDEA-13](ideas/IDEA-13_use_case_design.md)、[product/use_cases.md](product/use_cases.md)） | 完了 |
| サイクル13 | UC-1-1（特定企業の深掘り調査）実装。定性データ（事業概要・リスク）の追加、`facts`→`company_quantitative_facts`等の命名是正、個別ダウンロード機能とdocumentsテーブルの不整合是正 | 完了 |
| サイクル14 | ヘッダー背景色をブランドカラーに戻す（FR-61）。企業一覧画面（SCR-002）を全件初期表示から検索・業種絞り込み時のみ表示に変更し、業種絞り込み・並び順を追加（FR-62〜64） | 完了 |
| サイクル15 | UC-1-2（複数企業の比較）実装。比較企業選択画面（SCR-005）・比較結果画面（SCR-006）・ランキング画面（SCR-007）・ランキングAPI（API-COM-007）を新規追加（FR-65〜69） | 完了 |
| 次サイクル | 未定。`use_cases.md`のUC-1-3等から、画面フロー→画面→API→バッチの順で1件ずつ着手 | 企画待ち |

現時点で残っている大きな論点：
- アプリのコンセプト（サイクル11）・ユースケース一覧（サイクル12）がいずれも確定し、
  サイクル13でUC-1-1（特定企業の深掘り調査）、サイクル15でUC-1-2（複数企業の比較）を
  実装した。以降のサイクルも`docs/product/use_cases.md`のユースケース単位（UC-x-x）
  で機能を設計・実装する
  （[cycle-workflow](../.claude/skills/cycle-workflow/SKILL.md)参照）。
  [IDEA-10](ideas/IDEA-10_report_purpose_redesign.md)（画面の再設計）は各ユースケース
  実装サイクルの「画面の整理」ステップに組み込まれる想定
- サイクル13でSCR-004（保存済みデータ確認画面）・API-COM-004を削除した
  （ユースケースに紐づかない開発者向け機能と判断）。定性データの表示品質
  （EDINET CSV変換時点で表構造が失われる制約）への対応は
  [requirements/cycleX_backlog.md](requirements/cycleX_backlog.md)へ送った
- `use_cases.md`のUC-1-5・UC-3-4・UC-3-5は株価データ取得基盤（未着手、
  [IDEA-12](ideas/IDEA-12_stock_price_check.md)が関連）に依存し、UC-3-3はUC-1-4
  （定点観測）に依存するため、着手順序を検討する際は注意する
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
| ユースケース一覧（UC-x-x、以降のサイクルの着手単位） | [product/use_cases.md](product/use_cases.md) |
| ユースケース詳細（画面遷移・関連機能・依存関係） | [product/use_case_details/](product/use_case_details/) |
| まだ検討中のアイデア | [ideas/README.md](ideas/README.md) |
| 「やる」と決まったが未着手の事項 | [requirements/cycleX_backlog.md](requirements/cycleX_backlog.md) |
| 会計・EDINETのドメイン知識 | [domain/](domain/) |
| 日付表記のルール | [development/date_format_policy.md](development/date_format_policy.md) |
