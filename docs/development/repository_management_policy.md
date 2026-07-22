# リポジトリ管理方針

個人開発（レビュー者不在）であることを前提に、運用コストを最小化する方針で決定した内容を記録する。

---

## 1. リポジトリ構成：モノレポ

`backend/`・`frontend/`・`docs/`・`memo/` を1つのリポジトリ（このリポジトリ）で管理する。

**理由**
- フロントエンドとバックエンドは`docs/design/api/`のスキーマを介して密結合しており、
  API変更時に両方を同じコミット・同じPRで揃えられるモノレポの方が整合を保ちやすい
- CI/CDをリポジトリ単位で分ける必要があるほどの規模ではない
- 設計ドキュメント（`docs/`）とコードを同じ場所で管理することで、
  「どの設計に基づく実装か」を追跡しやすくする

---

## 2. ブランチ戦略：main直接運用

**`main`ブランチに直接コミットする。featureブランチ・PRは作らない。**

**理由**
- 個人開発でレビュー者がいないため、PRを介す運用はオーバーヘッドにしかならない
- 実際にこれまでの設計フェーズのコミットも`main`直接で行っており、実態に合わせた

**運用ルール**
- コミット単位は機能・ドキュメント単位で小さく切る（1コミット1目的）
- 動作しない状態やbroken buildを`main`に残さない（コミット前に最低限の動作確認をする）
- 大きめの変更（DBスキーマ変更、破壊的なAPI変更等）に着手する前は、
  作業前の状態を一度コミットしておく（今回`8abca30`の直前に設計成果物をコミットしたのと同様の運用）

---

## 3. コミット規約

[Conventional Commits](https://www.conventionalcommits.org/)の接頭辞をゆるく採用する（厳密なツール連携はしない、目視でのわかりやすさ重視）。

| プレフィックス | 用途 |
|---|---|
| `feat:` | 新機能追加 |
| `fix:` | バグ修正 |
| `docs:` | ドキュメントのみの変更（`docs/`・`memo/`） |
| `chore:` | 依存更新・設定変更など機能に影響しない変更 |
| `refactor:` | 挙動を変えないコードの整理 |

コミットメッセージは日本語で「Why」を書く（このリポジトリのこれまでのコミットメッセージ運用と同じ）。

---

## 4. 依存パッケージのバージョン固定ルール

| 対象 | 方針 |
|---|---|
| バックエンド `requirements.txt` | `pip freeze` で**完全固定**（`==`指定）。`pip install`のたびに環境が変わることを防ぐ。メジャーバージョンを上げる時だけ手動で更新する |
| フロントエンド `package.json` / `pnpm-lock.yaml` | `package.json`は`^`（マイナー範囲）で管理し、`pnpm-lock.yaml`を**必ずコミット**して実際のインストールバージョンを固定する（[frontend_implementation_policy.md](frontend_implementation_policy.md)のとおりpnpmを採用しているため、npmの`package-lock.json`は生成しない） |
| Python本体 | `python3.10`（Homebrew）に固定。`.python-version`等のバージョン指定ファイルは現時点では作らない（個人開発でPython切り替えの需要が低いため） |

---

## 5. 環境変数・シークレット管理

- 実際の値（`backend/.env`）は`.gitignore`で除外済み（コミットしない）
- **`backend/.env.example`を新規に作成し、コミットする**。キー名だけを記載し、値はプレースホルダーにする：
  ```
  EDINET_API_KEY=your_api_key_here
  DATABASE_URL=sqlite:///./financials.db
  ```
- 新しい環境変数を追加した場合は、`.env`と`.env.example`の両方を更新するルールとする（片方だけ更新して後で気づかない、という事故を防ぐ）
- APIキーなどの秘密情報は、コミットメッセージ・ドキュメント（`docs/`・`memo/`）にも直接書かない（今回のEDINET APIキーもメモには「`.env`の`EDINET_API_KEY`」という参照のみで、実際の値は記載していない）

---

## 参照
- [backend_implementation_policy.md](backend_implementation_policy.md)
- [frontend_implementation_policy.md](frontend_implementation_policy.md)
