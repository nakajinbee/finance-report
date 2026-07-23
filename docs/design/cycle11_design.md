# サイクル11 設計書

対象：[cycle11_requirements.md](../requirements/cycle11_requirements.md) FR-55

実装順：`docs/product/concept.md`の作成 → `docs/INDEX.md`のディレクトリ構成更新 →
`IDEA-14`の状態更新 → `cycleX_backlog.md`への優先度追記。コード変更は発生しない。

---

## 1. `docs/product/concept.md`の構成

`docs/design/design_guideline.md`と同じ位置づけ（常に最終断面のみを書く参照
ドキュメント。決定に至った経緯・議論の過程は書かない）にする。構成：

```markdown
# アプリコンセプト

## 想定利用者
## 提供価値
## 開発方針（dogfooding）
## 事業化スタンス
## 今後のサイクルへの示唆
```

`design_guideline.md`が「サイクル4では〜だった」のような時系列の記述を禁止して
いるのと同様の運用ルールを踏襲し（[design-apply](../../.claude/skills/design-apply/SKILL.md)
参照）、決定の経緯（サイクル11でこう決まった、という話）は
`cycle11_requirements.md`側に残し、`concept.md`自体には最終決定事項のみを書く。

## 2. `docs/INDEX.md`の更新

「ディレクトリ構成」に`docs/product/`を追加する：

```diff
 ├── design/                               ← 設計
 │   ├── self_review_rule.md
 │   ├── design_guideline.md               ← 本番デザインコンセプト（配色・タイポグラフィ等、常に最終断面のみ）
+│
+├── product/                              ← プロダクトコンセプト
+│   └── concept.md                        ← 想定利用者・提供価値・事業化スタンス（常に最終断面のみ）
```

「現在のフェーズ」にサイクル11の行を追加し、`docs/product/concept.md`への
クイックリンクも追加する。

## 3. `IDEA-14`・`cycleX_backlog.md`の更新

- `IDEA-14_business_concept_definition.md`の状態を「完了（サイクル11）」に更新し、
  `concept.md`へのリンクを追記する
- `cycleX_backlog.md`の「テキスト開示（事業の内容等）の保存・検索」項目に、
  コンセプト確定（定性的分析も提供価値に含む）により優先度が上がりうる旨を
  追記する。実装はスコープ外のままとする

---

## 4. 変更ファイル一覧

| ファイル | 変更内容 |
|---|---|
| `docs/product/concept.md` | 新規（コンセプト本体） |
| `docs/INDEX.md` | ディレクトリ構成・現在のフェーズ・クイックリンクの更新 |
| `docs/ideas/IDEA-14_business_concept_definition.md` | 状態を完了に更新 |
| `docs/requirements/cycleX_backlog.md` | テキスト開示項目に優先度上昇の記録を追記 |

コードの変更ファイルはなし。

## 5. 動作確認方針

コード変更がないため`tsc`/`oxlint`等は対象外。既存のバックエンド・フロントエンドが
引き続き正常応答することを`curl`で確認する（念のための回帰確認）。
