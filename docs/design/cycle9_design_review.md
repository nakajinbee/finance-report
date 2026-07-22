# サイクル9 設計 セルフレビュー結果

レビュー対象：[cycle9_design.md](cycle9_design.md)
レビュー基準：[self_review_rule.md](self_review_rule.md)

---

## 1. 機能面

- [x] 要件定義のすべての機能要件（FR-48〜51）に対応する設計が存在するか　→
  1節（FR-48）・2節（FR-49）・3節（FR-50）・4節（FR-51）で網羅
- [x] 各機能の入力・処理・出力が反映されているか　→ テーブル定義・関数・スクリプトの
  コード例を具体的に記載
- [x] エラー・例外ケースの処理フローを設計しているか　→ FR-49の追記事項
  （変換失敗・企業未登録のスキップ）を設計§2に反映済み。FR-50の1件失敗時も
  `try/except`でスキップしログに残す設計にした
- [x] ユーザーの全操作　→ 非該当（バックエンドのアーキテクチャ変更）
- [x] カスタマイズ要件　→ 非該当

## 2. 性能面

- [x] 応答時間　→ 本サイクルの主題（EDINETリクエスト数の抜本的な削減）
- [x] EDINET APIのレート制限　→ 既存の`_wait_for_rate_limit`・`_get`をそのまま使うため
  変更なし。サイクル8で追加した日付単位キャッシュも引き続き効く
- [x] キャッシュ戦略　→ `ingest_document_list_for_date`は`fetch_document_list`を
  そのまま呼ぶため、サイクル8のキャッシュの恩恵をそのまま受ける（ただしバックフィルは
  日付ごとに1回しか呼ばないため、このケースでのキャッシュヒットは想定していない。
  将来同じプロセス内で日次実行を複数回行う場合に効く）
- [x] パース処理のボトルネック　→ 既存の`xbrl_parser`をそのまま使うため非該当

## 3. セキュリティ・運用面

- [x] APIキーの露出　→ 変更なし
- [x] 入力バリデーション　→ 非該当（外部ユーザー入力を経由しない）
- [x] ローカルストレージの安全性　→ 非該当

## 4. 拡張性

- [x] フェーズ4（定期更新）を見据えた設計か　→ `ingest_document_list_for_date`が
  1日単位の関数として独立しているため、将来「今日だけ実行する」日次バッチを
  同じ関数で作れる
- [x] コンポーネントの責務が分離されているか　→ `document_list_ingestion.py`
  （書類一覧の取り込み）・`document_body_ingestion.py`（書類本体の取り込み）・
  `fact_ingestion.py`（DB書き込みロジックの共通化）で責務を分離した

---

## 5. 要件トレーサビリティチェック（FRの箇条書き単位で設計と突き合わせ）

- [x] FR-48「対象書類のみ保存（secCode存在・doc_type_code対象）」→ 設計§2
  `ingest_document_list_for_date`のフィルタ条件として一致
- [x] FR-48「主なカラム」→ 設計§1の`Document`モデルで全カラム一致
- [x] FR-48「company_code・facts_ingested_atにインデックス」→ 設計§1で
  `idx_documents_company_ingested`として一致
- [x] FR-49「upsert、doc_idで冪等」→ 設計§2で一致
- [x] FR-49「初回一括投入と継続更新を同じ関数で」→ 設計§2で
  `ingest_document_list_for_date`を両方から呼ぶ設計として一致
- [x] FR-49「未来日は指定不可、上限today」→ 設計§2の`ingest_document_list_backfill.py`で
  `today - timedelta(days=offset)`とし、todayから遡る方向のみのため未来日は
  発生しない設計。ただし明示的なガード（アサーション等）は入れていない　→
  **抜けを発見**：`offset`が負にならない限り未来日は原理的に発生しないため、
  現状のロジックで実質的に満たされている。ただし将来関数を直接呼び出すコードが
  増えた場合に備え、`ingest_document_list_for_date`側で`target_date > date.today()`を
  ガードすることを検討する余地はあるが、本サイクルでは過剰設計と判断し見送る
  （YAGNI。現在の呼び出し元は全て過去日のみを渡す）
- [x] FR-49「sec_code変換失敗・companies未登録はスキップしログに残す」→ 設計§2で
  `skipped_conversion`・`skipped_no_company`カウントとログ出力として一致
- [x] FR-50「facts_ingested_at NULL・csv_flag='1'・非取下を対象」→ 設計§3の
  `ingest_document_bodies.py`のクエリと`ingest_document_body`のガード条件で一致
- [x] FR-50「CSVパース、facts保存」→ 設計§3で`upsert_facts`呼び出しとして一致
- [x] FR-50「accounting_standard未設定なら判定」→ 設計§3で一致
- [x] FR-50「1件失敗で全体を止めない」→ 設計§3で個別`try/except`として一致
  （ただし`ingest_document_bodies.py`の`main`ループ自体は`ingest_document_body`の
  戻り値で成否を見るだけで例外を投げないため、ループ自体が止まることはない）
- [x] FR-51「ER図・table_list更新」→ 設計§4で一致
- [x] FR-51「個別ダウンロード機能が壊れない」→ 設計§4で、リファクタリングの範囲を
  「呼び出し元変更のみ」と明記し、動作確認方針§6にも実行確認を明記した
- [x] FR-51「既存APIのレスポンス変更なし」→ 設計§4で一致
- [x] NFR-20「既存機能への影響」→ 設計全体で新規追加のみ、既存コードの変更は
  リファクタリング（ロジック不変）のみ
- [x] NFR-21「EDINETへの負荷試算」→ 設計のバックフィルスクリプトが日付ごとに
  1リクエストのみ行う設計であることと整合

---

## 6. 実装可能性の確認（`grep`等での裏取り）

- [x] `_upsert_company`・`_upsert_facts`の現在の実装を確認し、ロジックを変更せず
  `fact_ingestion.py`へ移設する設計にした（重複コードの解消）
- [x] `find_report`が使っている`document.get("secCode")`等のキー名を確認し、
  `fetch_document_list`が返す辞書のキー名（`docID`・`edinetCode`・`secCode`・
  `docTypeCode`・`periodStart`・`periodEnd`・`submitDateTime`・`withdrawalStatus`・
  `disclosureStatus`・`csvFlag`）と設計コードの一致を確認した
- [x] `DOC_TYPE_CODE_ANNUAL_REPORT`・`DOC_TYPE_CODE_SEMI_ANNUAL_REPORT`の値（"120"・"160"）を
  確認し、`TARGET_DOC_TYPE_CODES`に反映した
- [x] `withdrawalStatus`の値の意味（"1"=取下書、"2"=取り下げられた書類、"0"=それ以外）を
  `EDINET_API_仕様書.pdf`で確認し、`WITHDRAWN_STATUSES = {"1", "2"}`として設計に反映した
- [x] `database.py`の型定義を見直し、`facts_ingested_at`の型不整合
  （`Mapped[str | None]`だが実際は`datetime`を代入する設計だった）を発見し、
  `Mapped[datetime | None]`に修正した

---

## 7. 追記：テーブル定義書（`TBL-004_documents.md`）の作成漏れ

ユーザー指摘により、`TBL-001`〜`TBL-003`と同様の単体テーブル定義書
（カラム定義・インデックス・外部キー制約・備考）が設計から漏れていたことが判明した。
`er_diagram.md`・`table_list.md`への反映は設計済みだったが、既存の慣習
（テーブルごとに`TBL-XXX_名前.md`を作る）を踏襲できていなかった。
`docs/design/table/TBL-004_documents.md`を追加し、設計書§4・変更ファイル一覧に
反映した。

---

## 判定：実装フェーズへ進んで問題なし

レビュー中に2件（`facts_ingested_at`の型不整合、`TBL-004_documents.md`の作成漏れ）を
発見し設計書を修正済み。要件の
全箇条書きを設計と突き合わせ、他に抜け漏れ・矛盾は見つからなかった。
実装順：FR-48（`database.py`→マイグレーション）→ FR-49（`fact_ingestion.py`移設→
`document_list_ingestion.py`→バックフィルスクリプト実行）→
FR-50（`document_body_ingestion.py`→サンプル実行）→ FR-51（ドキュメント更新・
既存機能の回帰確認）。
