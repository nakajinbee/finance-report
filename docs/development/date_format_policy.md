# 日付・時刻フォーマット統一ルール

バックエンド・フロントエンド・EDINET連携をまたいで日付の扱いが揺れないよう、
レイヤーごとに使う型とフォーマットを固定する。

---

## レイヤーごとの型・フォーマット

| レイヤー | 型・フォーマット | 例 | 備考 |
|---|---|---|---|
| DB（SQLAlchemy） | `Date`型（時刻を持たない） | `period_end` カラム | `TBL-003_facts.md`の`period_end`はカレンダー日付のみ。時刻は不要なので`DateTime`は使わない（サイクル2で`TBL-002_financials`から`TBL-003_facts`に置き換わったが、`period_end`の型・意味は変わらず継続） |
| バックエンド内部（Python） | `datetime.date`固定 | `date(2026, 3, 31)` | `database.py`の`period_end`と同じ型で統一する。時刻情報を持つ値（後述のEDINET提出日時など）が必要になった場合のみ`datetime.datetime`を使い、`date`と混在させない |
| 内部API（`docs/design/api/openapi.yaml`） | ISO 8601 日付形式（`format: date`）＝`YYYY-MM-DD` | `"2023-03-31"` | `FinancialRecord.period_end`と同じ表現。現状のスコープでは時刻付きのフィールドは内部APIに存在しない |
| EDINET APIから受け取る値 | 日付：`YYYY-MM-DD` ／ 日時：`YYYY-MM-DD hh:mm`（EDINET仕様上すべてJST） | `"2026-06-19 15:30"`（`submitDateTime`等） | EDINETの仕様どおりの文字列としてパースし、DB格納時に`date`型（時刻部分は捨てる）へ変換する。詳細は`memo/リクルートデータ取得メモ.md`参照 |
| タイムゾーン | すべてJST固定。UTC変換・`tzinfo`付与は行わない | ― | 対象企業・データソース（EDINET）が日本国内のため、UTC変換の必要性がない。将来複数タイムゾーン対応が必要になった場合のみ再検討する |
| フロントエンド表示用（会計年度） | 「YYYY年M月期」の日本語固定表記 | `"2026年3月期"` | `fiscal_year`（DBカラム／APIフィールド）にそのまま保持する値。`period_end`から画面側で動的に「年+M月期」を生成しない（EDINETの`docDescription`表記とズレるリスクを避けるため、取得時点で確定させた文字列をそのまま使う） |

---

## 禁止事項

- `date`と`datetime`を同じ意味の値に対して混在させない（例：`period_end`を`datetime.datetime`型で持たない）
- フロントエンド・バックエンドどちらでも、日付をUNIXタイムスタンプ（数値）でやり取りしない（可読性のためISO 8601文字列で統一）
- タイムゾーン変換処理（UTC⇄JST変換）を実装しない。すべてJSTとして扱う

---

## 参照

- [backend_implementation_policy.md](backend_implementation_policy.md)
- [frontend_implementation_policy.md](frontend_implementation_policy.md)
- [self_review_rule.md](self_review_rule.md)
- [../design/table/TBL-003_facts.md](../design/table/TBL-003_facts.md)
- [../../memo/リクルートデータ取得メモ.md](../../memo/リクルートデータ取得メモ.md)
