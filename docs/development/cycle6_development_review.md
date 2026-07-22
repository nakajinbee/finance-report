# サイクル6 開発 セルフレビュー結果

レビュー対象：FR-39〜41（全上場企業マスタの一括登録、フェーズ1）
レビュー基準：[self_review_rule.md](self_review_rule.md)
設計との対応確認：[docs/design/cycle6_design.md](../design/cycle6_design.md)

---

## 1. 設計の全実装チェック

| 設計項目 | 実装箇所 | 状態 |
|---|---|---|
| Alembicマイグレーション（accounting_standard NULL許容化） | `alembic/versions/6b364e253159_*.py` | [x] |
| `database.py`の`Company.accounting_standard`型変更 | `backend/database.py` | [x] |
| `schemas.py`の`Company.accounting_standard`型変更 | `backend/schemas.py` | [x] |
| `Company.yaml`の`nullable: true`化 | `docs/design/api/components/schemas/Company.yaml` | [x] |
| `TBL-001_companies.md`の更新 | 同ファイル | [x] |
| `list_all_filers()`公開関数の追加 | `backend/edinet_client.py` | [x] |
| `scripts/__init__.py`（パッケージ化） | `backend/scripts/__init__.py` | [x] |
| 一括登録バッチ本体 | `backend/scripts/bulk_register_companies.py` | [x] |
| `client.ts`の型変更 | `frontend/src/api/client.ts` | [x] |
| 一覧画面の代替表示 | `frontend/src/pages/CompanyListPage.tsx` | [x] |
| 詳細画面の代替表示・空状態UI | `frontend/src/pages/CompanyDetailPage.tsx` | [x] |

`git status`の変更ファイルが設計書§4の一覧と一致することを確認した。

---

## 2. 動作確認（実データで検証、モックなし）

- [x] マイグレーション適用：`alembic upgrade head`実行後、`PRAGMA table_info(companies)`で
  `accounting_standard`の`notnull`が`0`になったことを確認。既存14件のデータも保持されたまま
  （マイグレーションによるデータ欠損なし）
- [x] 一括登録バッチ実行：`python -m scripts.bulk_register_companies`を実行し、
  **登録/更新=3,829件、sec_codeなしでスキップ=7,522件、エラー=0件**を確認
- [x] DB内容確認：登録後の`companies`テーブルは全3,829件、うち`accounting_standard`が
  設定済みなのは既存の14件のみ（サイクル5以前にダウンロード済みだった企業）、残り3,815件は
  `NULL`。既存企業（リクルートHD、code=6098）の`accounting_standard`（IFRS）が
  上書きされず保持されていることを確認
- [x] API確認：`GET /api/companies`で3,829件・`accounting_standard: null`を含む
  レスポンスを確認。`GET /api/companies/{code}/financials`で財務データ未取得の企業
  （例：code=130A）に対し`data: []`・`accounting_standard: null`が正しく返ることを確認
  （エラーにならず空配列で返る）
- [x] `npx tsc -b --noEmit`・`npx oxlint`が通ることを確認（無出力＝エラーなし）
- [x] vite HMRログにエラーが出ていないことを確認
- [x] バックエンド・フロントエンドがともに`200`で応答することを確認
- [ ] ブラウザでの実際の見た目（空状態UIの表示、一覧の「データ未取得」表示）の
  目視確認は本環境にブラウザ操作ツールがなくできていない。ユーザー側での確認を推奨する

---

## 3. 実装中に発見・修正した設計外の問題

設計レビュー完了後、実装直前の最終確認として`edinet_client.list_all_filers()`を
実際に呼び出して`sec_code`の形式を確認したところ、**設計段階で見落としていた問題**を発見した。

- **`sec_code`は5桁（末尾`0`）、`companies.code`は4桁**：既存の`TBL-001_companies.md`には
  この変換ルール自体は記載されていたが、`cycle6_design.md`の初回設計では
  `Company(code=filer.sec_code)`と5桁のまま登録する設計になっており、既存の4桁キー体系と
  一致しない状態だった。実装前に実データ（3,829件）で全件が末尾`0`であることを確認した上で、
  `_to_company_code()`という変換関数を設計・実装に追加し、5桁→4桁変換を組み込んだ
- 変換後も3,829件すべてがユニークであることを実データで確認し、重複によるデータ上書き事故が
  ないことを確認した
- `TBL-001_companies.md`の備考に、この変換ルールを全銘柄で検証済みである旨を追記した
  （従来「4社のみで確認、全銘柄網羅的検証はしていない」という記載だったものを更新）

この問題は、要件定義・設計セルフレビューのいずれの段階でも「`_load_filer_info_cache`/
`list_all_filers`を実際に呼び出してデータの中身を見る」ことをしておらず、
`FilerInfo.sec_code`の実際のフォーマットを確認しないまま設計を進めたために発生した。
実装直前に実データを見て発見できたため実害はなかったが、次回以降は設計段階で
「使用する外部データの実際の値」を早い段階で確認するべきという教訓が残る。

---

## 4. コード品質

- [x] 型ヒント・TypeScript型定義を完備（`Company.accounting_standard: str | None` /
  `string | null`）
- [x] バッチ処理はエラー時にスキップしてログに残し、全体を止めない設計を実装した
- [x] `accounting_standard`を意図的に上書きしないロジックにコメントで理由を明記した
- [x] 不要なデバッグログなし
- [x] 日付・時刻の扱い　→ 本サイクルは対象外（変更なし）

---

## 判定：テストフェーズ（実機での最終確認）へ移行可能

設計通りに実装済み。実装直前に発見した`sec_code`変換漏れは、実データによる検証で
発見・修正済みで実害はなかった。バックエンドは実データ（EDINETコードリスト全件、
3,829社）で動作確認済み。フロントエンドの目視確認はユーザー側推奨。
