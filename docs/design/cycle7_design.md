# サイクル7 設計書

対象：[cycle7_requirements.md](../requirements/cycle7_requirements.md) FR-42〜44
（フェーズ2：少数企業でのバッチ取得の技術検証）

実装順：FR-42（リクエストカウンタ）→ FR-43（検証スクリプト・実行）→ FR-44（見積もりドキュメント）

---

## 1. FR-42：EDINETリクエスト回数の計測

### `backend/edinet_client.py`

```diff
  _last_request_time: float = 0.0
+ _request_count: int = 0
```

```python
def get_request_count() -> int:
    """直近のreset_request_count()以降に行われたEDINETへのHTTPリクエスト回数を返す
    （サイクル7 FR-42、バッチ取得の技術検証用）"""
    return _request_count


def reset_request_count() -> None:
    """リクエストカウンタを0に戻す（企業ごとに区切って計測するため）"""
    global _request_count
    _request_count = 0
```

`_get`関数の先頭でカウンタをインクリメントする：

```diff
  def _get(path: str, params: dict) -> requests.Response:
      _wait_for_rate_limit()
      global _last_request_time
+     global _request_count
+     _request_count += 1
      response = requests.get(
```

`FILER_INFO_URL`（EDINETコードリスト）は`_get`を経由しない別関数（`requests.get`直呼び）の
ため、このカウンタには含まれない（レート制限対象外であることが既にコメントで明記されて
おり、リクエスト回数計測の対象は「レート制限のかかる本APIへのリクエスト」に絞るという
既存の区別と整合する）。

### 変更に伴う`backend/scripts/bulk_register_companies.py`への影響確認

`_to_company_code`は本サイクルでも別スクリプトから必要になるため、重複を避けて
`edinet_client.py`に移設する：

```diff
- def _to_company_code(sec_code: str) -> str:  # bulk_register_companies.py内で削除
+ # edinet_client.pyに移設し、公開関数化
```

```python
def to_company_code(sec_code: str) -> str:
    """EDINETの証券コード（5桁、末尾0）を、companiesテーブルの4桁codeに変換する
    （サイクル6 FR-39で追加、サイクル7 FR-43でも共用するためedinet_client.pyに移設）。
    """
    if not sec_code.endswith("0"):
        raise ValueError(f"末尾が0でない証券コード: {sec_code}")
    return sec_code[:-1]
```

`bulk_register_companies.py`は`from edinet_client import list_all_filers, to_company_code`に
変更し、独自定義していた`_to_company_code`を削除する（ロジックは変更しない、呼び出し元の
importのみ変更）。

---

## 2. FR-43：サンプル企業でのバッチ取得検証スクリプト

### サンプル選定方針

- `companies`テーブルから業種（`sector`）ごとに1社ずつ、業種名の昇順で先頭の20業種を選ぶ
  （34業種中20業種、各業種の中では`code`昇順で最初の1社）。特定の業種・規模に偏った
  サンプルにならないようにするための簡便な方法として採用する
- 追加で、意図的に「書類が見つかりにくそう」な小規模企業を2〜3社手動で加える
  （具体的な企業は実装時にDBの内容を見て選定する。例：直近上場・整理銘柄に近い企業等）

### `backend/scripts/verify_batch_timing.py`（新規）

```python
"""少数企業でバッチ取得の所要時間・EDINETリクエスト回数を実測する
（サイクル7 FR-43、IDEA-01フェーズ2）。

実行方法：backend/ディレクトリで `python -m scripts.verify_batch_timing`
"""
import logging
import time

import edinet_client
import schemas
from database import Company, SessionLocal
from routers.edinet import _states, run_download_job

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

SAMPLE_SECTOR_LIMIT = 20


def select_sample_companies(session) -> list[Company]:
    """業種ごとに1社（code昇順で先頭）を、業種名の昇順でSAMPLE_SECTOR_LIMIT件選ぶ"""
    companies = session.query(Company).order_by(Company.sector, Company.code).all()
    seen_sectors: set[str | None] = set()
    sample: list[Company] = []
    for company in companies:
        if company.sector in seen_sectors:
            continue
        seen_sectors.add(company.sector)
        sample.append(company)
        if len(sample) >= SAMPLE_SECTOR_LIMIT:
            break
    return sample


def find_edinet_code(company_code: str) -> str | None:
    """companies.code（4桁）に対応するedinet_codeをEDINETコードリストから逆引きする"""
    for filer in edinet_client.list_all_filers():
        if filer.sec_code is not None and edinet_client.to_company_code(filer.sec_code) == company_code:
            return filer.edinet_code
    return None


def main() -> None:
    with SessionLocal() as session:
        sample = select_sample_companies(session)

    results = []
    for company in sample:
        edinet_code = find_edinet_code(company.code)
        if edinet_code is None:
            logger.warning("edinet_codeが見つかりません: code=%s", company.code)
            continue

        _states[company.code] = schemas.DownloadStatus(
            status=schemas.DownloadOverallStatus.IN_PROGRESS, logs=[]
        )
        edinet_client.reset_request_count()
        start = time.perf_counter()
        run_download_job(company.code, edinet_code, schemas.DownloadPeriod(type="all"))
        elapsed = time.perf_counter() - start

        state = _states[company.code]
        results.append((company.code, company.name, elapsed, edinet_client.get_request_count(), state.status))
        logger.info(
            "code=%s name=%s 所要時間=%.1f秒 リクエスト数=%d ステータス=%s",
            company.code, company.name, elapsed, edinet_client.get_request_count(), state.status,
        )

    total_seconds = sum(r[2] for r in results)
    total_requests = sum(r[3] for r in results)
    logger.info(
        "=== 集計：%d社、合計%.1f秒、合計%dリクエスト、1社あたり平均%.1f秒/%.1fリクエスト ===",
        len(results), total_seconds, total_requests,
        total_seconds / len(results) if results else 0,
        total_requests / len(results) if results else 0,
    )


if __name__ == "__main__":
    main()
```

**設計判断のポイント**：

- `run_download_job`はFastAPIの`BackgroundTasks`経由で呼ばれる想定の通常の同期関数であり、
  HTTPサーバーを介さずスクリプトから直接importして呼び出せる。サーバー起動・
  `POST /api/download`＋ポーリングの往復を避けられ、検証スクリプトをシンプルにできる
  （実行されるロジック自体は本番のAPIエンドポイントと完全に同一）
- `_states`辞書へのエントリ登録は、通常`routers/edinet.py`のAPIハンドラが行っている処理を
  スクリプト側で再現する必要がある（`run_download_job`は`_states[company_code]`が
  事前に存在する前提のため）
- `period.type="all"`（全期間）を対象にする。既存の`_determine_target_fiscal_years`が
  企業の決算日から自動的に取得可能な最大年数を算出するため、スクリプト側で年数を
  指定する必要はない

---

## 3. FR-44：全社展開時の所要時間見積もりドキュメント

### `docs/development/cycle7_batch_timing_estimate.md`（新規）

FR-43の実行結果（ログ出力）をもとに、以下の内容を記載する（実装セルフレビューのタイミングで
実測値を反映して作成する。ひな形として設計時点で構成のみ示す）：

```markdown
# サイクル7：全社展開時の所要時間見積もり

## 実測結果（サンプルN社）
（各社の所要時間・リクエスト数の一覧、平均・最大値）

## 全社展開（3,829社）時の試算
（平均値 × 3,829社、最大値 × 3,829社の両方を示す）

## 評価
（試算結果が実務上許容できる時間か。許容できない場合の対応案）

## フェーズ3への申し送り事項
（並列化・探索窓の縮小・書類日付の事前キャッシュ等、検討すべき対応があれば列挙）
```

---

## 4. 変更ファイル一覧

| ファイル | 変更内容 | 関連FR |
|---|---|---|
| `backend/edinet_client.py` | リクエストカウンタ・`to_company_code`の追加/移設 | FR-42 |
| `backend/scripts/bulk_register_companies.py` | `_to_company_code`を`edinet_client.to_company_code`の利用に変更 | FR-42 |
| `backend/scripts/verify_batch_timing.py` | 検証スクリプト（新規） | FR-43 |
| `docs/development/cycle7_batch_timing_estimate.md` | 見積もりドキュメント（新規） | FR-44 |

---

## 5. 動作確認方針

- `backend/scripts/verify_batch_timing.py`を実際に実行し、20社程度の実データで
  所要時間・リクエスト数を計測する（モックなし）
- 既存のダウンロード機能（`POST /api/download`経由の通常フロー）が、
  `run_download_job`の変更（実質的な変更なし、呼び出し元が増えるのみ）によって
  壊れていないことを確認する
