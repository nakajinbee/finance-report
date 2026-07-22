# アイデア一覧

まだサイクルの要件として確定していない、検討段階のアイデアを置く場所。
`docs/requirements/cycleX_backlog.md`との違い：

| | `docs/ideas/` | `cycleX_backlog.md` |
|---|---|---|
| 状態 | まだ検討中・やるかどうか未確定 | 「やる」と決まっているが未着手 |
| 発生元 | 思いついた時点で自由に追加 | サイクルの要件定義でスコープ外にした事項 |
| 次のアクション | ユーザーと相談して、やる／やらない／保留を判断する | 次のサイクルの要件定義に組み込む |

アイデアが「やる」と決まったら、`cycleX_backlog.md`に移すか、直接そのサイクルの
`cycleN_requirements.md`に組み込み、`docs/ideas/`からは削除する。「やらない」と決まった
アイデアも、判断根拠を一言添えて削除してよい（ここは検討中のものだけを置く場所であり、
却下履歴のアーカイブではない）。

新しいアイデアを追加するときは`_template.md`をコピーして使う。

---

## 一覧

| ID | タイトル | 優先度 | いつ反映するか | ファイル |
|---|---|---|---|---|
| IDEA-01 | データ取得方式の刷新（都度参照→一括DB化） | 未定 | 未定 | [IDEA-01_db_batch_ingestion.md](IDEA-01_db_batch_ingestion.md) |
| IDEA-02 | 企業一覧：検索結果のみ表示 | 未定 | 未定 | [IDEA-02_company_list_search_only.md](IDEA-02_company_list_search_only.md) |
| IDEA-03 | 企業一覧：ソート機能 | 未定 | 未定 | [IDEA-03_company_list_sort.md](IDEA-03_company_list_sort.md) |
| IDEA-04 | 企業一覧：業界絞り込み | 未定 | 未定 | [IDEA-04_company_list_sector_filter.md](IDEA-04_company_list_sector_filter.md) |
| IDEA-05 | 企業比較ページ | 低 | 未定 | [IDEA-05_company_comparison_page.md](IDEA-05_company_comparison_page.md) |
| IDEA-06 | 業界ごとのシェア地図 | 低 | 未定 | [IDEA-06_sector_share_map.md](IDEA-06_sector_share_map.md) |
| IDEA-07 | ユーザー管理・ログイン機能 | 未定 | 未定 | [IDEA-07_user_management_login.md](IDEA-07_user_management_login.md) |
| IDEA-08 | Jira（＋Confluence検討）でのプロジェクト管理 | 未定 | 未定 | [IDEA-08_jira_project_management.md](IDEA-08_jira_project_management.md) |
| IDEA-09 | テストコードの整備 | 未定 | 未定 | [IDEA-09_test_coverage.md](IDEA-09_test_coverage.md) |
| IDEA-10 | レポート表示の強化（コンセプト起点の再設計） | 未定 | コンセプト決定後 | [IDEA-10_report_purpose_redesign.md](IDEA-10_report_purpose_redesign.md) |
| IDEA-11 | 生成AIとの連携（レポートQA機能） | 未定 | IDEA-07の後 | [IDEA-11_ai_report_qa.md](IDEA-11_ai_report_qa.md) |
| IDEA-12 | 株価確認機能 | 未定 | 未定 | [IDEA-12_stock_price_check.md](IDEA-12_stock_price_check.md) |
| IDEA-13 | ユースケース設計 | 未定 | コンセプト決定後 | [IDEA-13_use_case_design.md](IDEA-13_use_case_design.md) |
