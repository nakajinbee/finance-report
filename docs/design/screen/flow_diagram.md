# 画面遷移図

画面一覧は[screen_list.md](screen_list.md)参照。各画面の詳細な遷移条件は
各`SCR-XXX_*.md`本体に書く。このファイルは全体像を俯瞰するためのMermaid図のみを持つ
（常に最終断面。個々の遷移の理由・経緯は各画面ドキュメント側に書く）。

```mermaid
flowchart TD
    START(["アプリ起動"]) -->|DBが空| SCR001
    START -->|DBにデータあり| SCR002

    SCR001["SCR-001<br/>ダウンロード画面"] -->|ダウンロード開始 or 完了後のボタン| SCR002
    SCR002["SCR-002<br/>企業一覧画面"] -->|企業カードクリック| SCR003
    SCR002 -->|ヘッダーの「ダウンロード」ボタン| SCR001
    SCR003["SCR-003<br/>企業詳細画面"] -->|戻るリンク| SCR002

    HEADER["共通ヘッダー（全画面から常時アクセス可）"] -.->|ロゴ/企業一覧リンク| SCR002
```

## 備考

- 共通ヘッダーは全画面に表示され、ロゴ・「企業一覧」リンクから常にSCR-002へ
  戻れる（`frontend/src/components/Header.tsx`）
- 新しいユースケースの実装で新規画面・新規遷移が発生した場合、このMermaid図に
  ノード・矢印を追記する（[cycle-workflow](../../../.claude/skills/cycle-workflow/SKILL.md)の
  「画面フローの整理」ステップ）
