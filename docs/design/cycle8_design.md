# サイクル8 設計書

対象：[cycle8_requirements.md](../requirements/cycle8_requirements.md) FR-45〜47
（フェーズ3の前段：日付単位キャッシュ導入と再検証）

実装順：FR-45（キャッシュ実装）→ FR-46（再検証スクリプト・実行）→ FR-47（見積もり更新）

---

## 1. FR-45：`fetch_document_list`の日付単位キャッシュ

### `backend/edinet_client.py`

```diff
  _last_request_time: float = 0.0
  _request_count: int = 0
+ _document_list_cache: dict[date, list[dict]] = {}
```

```diff
  def fetch_document_list(target_date: date) -> list[dict]:
      """書類一覧API(type=2)を呼び、指定日の提出書類一覧(results)を返す

      書類一覧APIは成功・失敗どちらもHTTP 200で返るため、レスポンスJSON内の
      metadata.status で成否を判定する。
+
+     同一日付への2回目以降の呼び出しはプロセス内キャッシュから返す（サイクル8
+     FR-45）。異なる企業の`search_report`が同じ日付範囲を探索することが多く
+     （決算期が集中する3月末近辺等）、EDINETへの重複リクエストが多いことが
+     サイクル7の実測で判明したため。過去日の提出履歴は後から変わらないため、
+     キャッシュに陳腐化のリスクはない（本関数は未来日を渡されない前提。
+     `search_report`側で既に未来日を除外している）。
      """
+     if target_date in _document_list_cache:
+         return _document_list_cache[target_date]
+
      response = _get(
          "/documents.json",
          {"date": target_date.isoformat(), "type": 2},
      )
      body = response.json()
      status = body.get("metadata", {}).get("status")
      if status != "200":
          message = body.get("metadata", {}).get("message", "unknown error")
          raise EdinetApiError(f"書類一覧APIがエラーを返しました: status={status}, message={message}")
-     return body.get("results") or []
+     results = body.get("results") or []
+     _document_list_cache[target_date] = results
+     return results
```

**設計判断のポイント**：

- キャッシュキーは`date`オブジェクトそのもの（`_load_filer_info_cache`と同様、
  プロセス起動中は保持し続ける方針。上限・TTLは設けない。理由はFR-45要件文の通り
  YAGNI：探索対象日数が数千日オーダーに収まり、メモリ上問題にならないため）
- `EdinetApiError`が発生した場合（`status != "200"`）はキャッシュに書き込まない
  （一時的なエラーだった場合に、誤ったエラー結果を恒久的にキャッシュしてしまうことを
  避けるため。成功した結果のみキャッシュする）
- 呼び出し元（`search_report`）のコードは一切変更不要。`fetch_document_list`の
  シグネチャ・戻り値の意味は変わらないため

---

## 2. FR-46：キャッシュ導入後の再検証

### `backend/scripts/verify_batch_timing.py`

```diff
  def select_sample_companies(session) -> list[Company]:
      """業種ごとに1社（code昇順で先頭）を、業種名の昇順でSAMPLE_SECTOR_LIMIT件選ぶ"""
-     companies = session.query(Company).order_by(Company.sector, Company.code).all()
+     # accounting_standardが未設定（＝財務データ未取得）の企業に限定する。
+     # 既に取得済みの企業を選ぶと、FR-11のスキップ判定により0秒・0リクエストという
+     # 無意味な結果になり、キャッシュの効果を測定できないため（サイクル8 FR-46）。
+     companies = (
+         session.query(Company)
+         .filter(Company.accounting_standard.is_(None))
+         .order_by(Company.sector, Company.code)
+         .all()
+     )
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
```

他のロジック（`find_edinet_code`・`main`）は変更しない。同じスクリプトを再実行するだけで
FR-46を満たす。

---

## 3. FR-47：改善効果の評価と見積もりの更新

`docs/development/cycle7_batch_timing_estimate.md`に「サイクル8：キャッシュ導入後の
再検証結果」という節を追記する（新規ファイルは作らず、既存の見積もりドキュメントを
更新して比較しやすくする）。記載する内容：

- サイクル7（キャッシュなし）とサイクル8（キャッシュあり）の実測値比較表
  （合計所要時間・合計リクエスト数・1社あたり平均）
- 削減率（%）
- 改善後の全社展開時間の再試算（サイクル7と同じ計算式：平均×未取得社数）
- 評価：実務上許容できる水準に達したか。達していない場合は次の高速化案
  （並列化等）を「フェーズ3本体への申し送り事項」として追記する

---

## 4. 変更ファイル一覧

| ファイル | 変更内容 | 関連FR |
|---|---|---|
| `backend/edinet_client.py` | `fetch_document_list`に日付単位キャッシュを追加 | FR-45 |
| `backend/scripts/verify_batch_timing.py` | サンプル選定条件に`accounting_standard IS NULL`を追加 | FR-46 |
| `docs/development/cycle7_batch_timing_estimate.md` | サイクル8の再検証結果を追記 | FR-47 |

---

## 5. 動作確認方針

- キャッシュ追加後、既存のダウンロード機能（個別企業の通常フロー）が壊れていないことを
  確認する（`fetch_document_list`の戻り値の型・内容は変わらないため、回帰は起きにくいが
  実データで確認する）
- `verify_batch_timing.py`を再実行し、実際にキャッシュヒットが発生していること
  （サイクル7と同規模のサンプルで、合計リクエスト数がサイクル7より明確に少ないこと）を
  実データで確認する
