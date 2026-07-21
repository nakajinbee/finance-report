# サイクル3 設計書

対象：[cycle3_requirements.md](../requirements/cycle3_requirements.md) FR-17〜19
（画面・API契約への変更なし。バックエンド内部のマッピング・パースロジックのみが対象）

前提となるドメイン知識：[docs/domain/xbrl_tagging_variability.md](../domain/xbrl_tagging_variability.md)

---

## 1. FR-17：候補element_idマッピング化（ローカル名照合）

### データ構造（`backend/metric_mappings.py`）

現行（サイクル2まで）：
```python
FIVE_METRICS: dict[str, dict[str, tuple[str, str]]]
# 例： "IFRS": {"revenue": ("jpcrp_cor:RevenueIFRSSummaryOfBusinessResults", "CurrentYearDuration")}
```

変更後：
```python
# 指標ごとのコンテキストID種別（会計基準・企業によらず一定）
METRIC_CONTEXT_ID: dict[str, str] = {
    "revenue": "CurrentYearDuration",
    "operating_profit": "CurrentYearDuration",
    "net_profit": "CurrentYearDuration",
    "total_assets": "CurrentYearInstant",
    "total_liabilities": "CurrentYearInstant",
}

# 値はローカル名（要素IDのコロン以降）の候補リスト。優先順位付き
FIVE_METRICS: dict[str, dict[str, list[str]]]
# 例： "IFRS": {"revenue": ["RevenueIFRSSummaryOfBusinessResults", "OperatingRevenuesIFRSKeyFinancialData"]}
```

`CASH_FLOW`も同様に`dict[str, dict[str, list[str]]]`へ変更する。`CASH_FLOW_CONTEXT_ID`
（`"CurrentYearDuration"`固定）はそのまま維持する（キャッシュフロー3項目はすべてduration概念のため、
`METRIC_CONTEXT_ID`のような指標別の出し分けは不要）。

候補リストの内容は[cycle3_requirements.md](../requirements/cycle3_requirements.md)の
FR-17に列挙した、実機検証済みのローカル名のみを追加する。

### マッチングロジック（`backend/routers/companies.py`）

```
_local_name(element_id) -> str
    element_id.split(":")[-1] を返す（名前空間プレフィックスを除いたローカル名）

_index_facts_by_period(facts) -> dict[period_end, dict[(local_name, context_id), value]]
    facts一覧を「期間ごとの (ローカル名, コンテキストID) → 値」の索引に変換する

_lookup_metric(period_index, candidates, context_id) -> value | None
    candidatesを優先順に、各候補について
    (candidate, context_id) → 見つからなければ (candidate, context_id + "_NonConsolidatedMember")
    の順で索引を引く。最初に見つかった値を返す（FR-18のフォールバックをここに統合する）
```

`_build_financial_records`・`_build_cash_flow_records`は、
`_index_facts_by_period`で作った索引に対し、指標ごとに`_lookup_metric`を呼ぶ形に変更する。
1件もマッチしない期間はこれまで通りレコード自体を作らない（サイクル2までの挙動を維持）。

### 入力・処理・出力

| 項目 | 内容 |
|------|------|
| 入力 | `Fact`一覧（DB、TBL-003）、会計基準（`Company.accounting_standard`） |
| 処理 | 上記マッチングロジックで指標ごとに値を検索 |
| 出力 | `FinancialRecord`・`CashFlowRecord`（サイクル2までと型・フィールドは変更なし） |
| 該当なしの場合 | 指標値は`None`（＝「データなし」、FR-03を踏襲、画面側の変更不要） |

---

## 2. FR-18：非連結コンテキストIDフォールバック

設計は上記`_lookup_metric`に統合済み（`metric_mappings.NON_CONSOLIDATED_CONTEXT_SUFFIX`という
定数名で`"_NonConsolidatedMember"`を定義し、ハードコードしない）。

**エラー・例外ケース**：連結・非連結どちらのコンテキストでも見つからない場合は、
FR-17と同じく「データなし」として扱う（新たな失敗モードを導入しない）。

**設計時の確認事項**：連結・非連結の判別は`facts.consolidated_or_individual`列
（CSVの「連結・個別」列をそのまま保存したもの）ではなく、**コンテキストIDの
`_NonConsolidatedMember`サフィックスの有無**で行う。実データを確認したところ、
`consolidated_or_individual`列は`_NonConsolidatedMember`コンテキストの行でも
`"個別"`・`"その他"`など値が一定しておらず（大本組で実機確認）、判別の根拠として
信頼できないことがわかったため。

---

## 3. FR-19：決算日「N月末日」表記への対応

### データ構造（`backend/edinet_client.py`）

```python
FISCAL_YEAR_END_LAST_DAY_OF_MONTH = 0  # 「月末」を表すセンチネル値（dayとしては無効な値のため衝突しない）
```

`FilerInfo.fiscal_year_end_day`はこれまで通り`int | None`のままとし、値として
`FISCAL_YEAR_END_LAST_DAY_OF_MONTH`（`0`）を取りうるようにする（型は変更しない。
`None`＝「決算日が不明」、`0`＝「月末日（具体的な日は年による）」を区別する）。

### 処理フロー

```
_parse_fiscal_year_end(raw: str) -> (month, day)
    1. "N月末日" パターンにマッチ → (month, FISCAL_YEAR_END_LAST_DAY_OF_MONTH)
    2. "N月N日" パターンにマッチ → (month, day)
    3. どちらにもマッチしない → (None, None)  ※サイクル2までと同じ、変更なし

fiscal_year_end_date(month, day, year) -> date
    dayがFISCAL_YEAR_END_LAST_DAY_OF_MONTHなら calendar.monthrange(year, month) で
    実際の月末日に解決してからdate()を構築する。それ以外はdayをそのまま使う
```

`edinet_client.py`・`routers/edinet.py`内で`date(year, month, day)`のように
`fiscal_year_end_day`を直接`date()`に渡している箇所（
`determine_latest_available_fiscal_year`・`fiscal_year_start`・`half_fiscal_year_end`・
`report_search_center`・`routers/edinet.py`の`_expected_period_end`）を、
すべて`fiscal_year_end_date()`経由に置き換える。

### エラー・例外ケース

- 「N月末日」「N月N日」以外の未知の表記　→ 従来通り`(None, None)`。ダウンロードフロー
  （FR-09、`routers/edinet.py`の`run_download_job`）は既存のエラーメッセージ
  「証券コードまたは決算日が不明なため、ダウンロードできません」を返す（変更なし）

---

## 4. FR-21：書類探索が未来日に達した場合の異常終了を修正

### 処理フロー（`backend/edinet_client.py`の`search_report`）

```
search_report(sec_code, around_date, doc_type_code, window_days=25):
    for offset in range(0, window_days + 1):
        for sign in ...:
            candidate_date = around_date + offset*sign日
            if candidate_date > date.today():
                continue  # ここを追加：未来日はEDINETに存在しないため問い合わせない
            documents = fetch_document_list(candidate_date)
            ...
```

`fetch_document_list`自体は変更しない（`metadata.status`が`"200"`以外なら例外を送出する
既存の挙動は、EDINET APIの仕様上正しい実装のため維持する）。`search_report`側で、
そもそも未来日を候補にしないようにすることで、無駄なAPI呼び出しと、それに伴う
探索の異常終了を防ぐ。

### エラー・例外ケース
- 探索窓（`around_date`±`window_days`）がすべて未来日になることは、決算日・提出期限の
  計算ロジック（`report_search_center`）上起こりえない（提出期限＝決算日から一定日数後で
  あり、探索窓はその近傍のため、探索窓の一部が未来日になることはあっても全部が未来日に
  なることはない）。全候補が未来日でスキップされた場合は、従来通り
  `EdinetDocumentNotFoundError`を送出する（ループが1件も`fetch_document_list`を呼ばずに
  終わった場合も、ループ後の例外送出ロジックは変更不要）

---

## 5. FR-22：APIキー無効時（401）のエラーメッセージ不備を修正

### データ構造・処理フロー（`backend/edinet_client.py`）

```python
class EdinetAuthError(EdinetApiError):
    """APIキーが無効な場合（401）"""

def _get(path, params) -> requests.Response:
    ...（既存の429チェック）...
    # 401はHTTPステータス200のまま、{"StatusCode": 401, "message": ...}という
    # metadataでラップされない形状で返る（他のエラーと異なる）
    try:
        body = response.json()
    except ValueError:
        body = None  # 書類取得APIの成功時（ZIPバイナリ）はJSONとして読めないため
    if isinstance(body, dict) and body.get("StatusCode") == 401:
        raise EdinetAuthError(f"EDINET APIキーが無効です: {body.get('message')}")
    return response
```

`_get`は`fetch_document_list`・`fetch_report_csv`の両方から呼ばれる共通処理のため、
ここで一括判定することで両APIの401ケースをまとめて解消する。呼び出し元
（`fetch_document_list`・`fetch_report_csv`）の既存の`metadata.status`判定ロジックは
変更しない（401以外はこれまで通り機能する）。

### エラー・例外ケース
- 401検知のために`response.json()`を試行するが、書類取得API成功時のレスポンス
  （ZIPバイナリ）はJSONとして解釈できず`ValueError`が送出される。この場合は
  `body = None`として後続の401判定をスキップし、通常の処理（呼び出し元でのContent-Type
  判定等）に進む
- `run_download_job`（FR-09、`routers/edinet.py`）は既存の`except Exception`で
  `EdinetAuthError`も捕捉するため、1件のエラーで全体が停止することはない
  （既存のエラーハンドリング方針を維持）

---

## 性能・セキュリティ・拡張性（self_review_rule.md 2〜4節）

- **性能**：`_lookup_metric`は候補リスト×コンテキスト2種の走査だが、候補数は指標あたり
  最大3件程度、1企業のfacts件数（数百〜数千件）に対して無視できるオーダー。EDINET APIの
  呼び出し回数・レート制限には影響しない（本サイクルはEDINET通信部分を変更しない）
- **セキュリティ**：新規の外部入力・新規APIエンドポイントを追加しないため、変更なし
- **拡張性**：候補リスト方式にしたことで、今後新しい企業で未知のタグが見つかった場合も
  `metric_mappings.py`にローカル名を1行追加するだけで対応できる（コード変更不要）。
  非連結コンテキストのフォールバックも指標ごとに個別実装せず共通化しているため、
  新しい指標を追加する際も自動的に適用される

---

## 6. FR-23〜26：財務分析指標の拡充

対象API：`GET /companies/{code}/ratios`（API-COM-005、新規）。SCR-003にCFグラフ・表と
同じ並びで新セクションとして追加する（ユーザー承認済み、[cycle3_requirements.md](../requirements/cycle3_requirements.md)参照）。

### データ構造（`backend/metric_mappings.py`に追加）

```python
# グループA：EDINET自己開示の比率（ローカル名候補リスト、FIVE_METRICSと同じ形式）
DISCLOSED_RATIOS: dict[str, dict[str, list[str]]] = {
    "IFRS": {
        "roe": ["RateOfReturnOnEquityIFRSSummaryOfBusinessResults"],
        "equity_ratio": ["RatioOfOwnersEquityToGrossAssetsIFRSSummaryOfBusinessResults"],
        "eps": ["BasicEarningsLossPerShareIFRSSummaryOfBusinessResults"],
        "per": ["PriceEarningsRatioIFRSSummaryOfBusinessResults"],
    },
    "Japan GAAP": {
        "roe": ["RateOfReturnOnEquitySummaryOfBusinessResults"],
        "equity_ratio": ["EquityToAssetRatioSummaryOfBusinessResults"],
        "eps": ["BasicEarningsLossPerShareSummaryOfBusinessResults"],
        "per": ["PriceEarningsRatioSummaryOfBusinessResults"],
        "payout_ratio": ["PayoutRatioSummaryOfBusinessResults"],
    },
    "US GAAP": {},  # 実装時に確認。未確認のため空で開始し、確認できた時点で追加する
}
DISCLOSED_RATIO_CONTEXT_ID = "CurrentYearDuration"  # 比率は期間概念のため（EPSも期間利益÷株数）

# グループC：計算に必要な追加のB/S項目（ローカル名候補リスト、METRIC_CONTEXT_IDと同様の考え方）
BALANCE_SHEET_ITEMS: dict[str, dict[str, list[str]]] = {
    "IFRS": {
        "current_assets": ["CurrentAssetsIFRS"],
        "current_liabilities": ["TotalCurrentLiabilitiesIFRS"],
        "non_current_assets": ["NonCurrentAssetsIFRS"],
        "equity": ["EquityIFRS"],
        "inventories": ["InventoriesCAIFRS"],
    },
    "Japan GAAP": {
        "current_assets": ["CurrentAssets"],
        "current_liabilities": ["CurrentLiabilities"],
        "non_current_assets": ["NoncurrentAssets"],
        "equity": ["NetAssets"],
        "inventories": ["Inventories"],
    },
    "US GAAP": {},  # FR-20と同じ理由（連結ベースの内訳が存在しない）で対象外
}
BALANCE_SHEET_CONTEXT_ID = "CurrentYearInstant"
```

`equity`（自己資本・純資産）はグループA「equity_ratio（開示値）」の代替計算にも、
グループC「fixed_ratio」「current_ratio」にも使う共通項目のため、`BALANCE_SHEET_ITEMS`に
一本化する。既存の`_lookup_metric`（ローカル名候補×非連結フォールバック）をそのまま流用する。

### 処理フロー（`backend/routers/companies.py`に追加）

```
_build_ratio_records(facts, accounting_standard):
    period_index = _index_facts_by_period(facts)  # FR-17で作成済みの関数を再利用
    financial_records = _build_financial_records(facts, accounting_standard)  # revenue等の取得に再利用
    financial_by_period = {r.period_end: r for r in financial_records}

    for period_end in sorted(period_index):
        disclosed = { ratio: _lookup_metric(period_index[period_end], candidates, DISCLOSED_RATIO_CONTEXT_ID)
                      for ratio, candidates in DISCLOSED_RATIOS[accounting_standard].items() }
        bs = { item: _lookup_metric(period_index[period_end], candidates, BALANCE_SHEET_CONTEXT_ID)
               for item, candidates in BALANCE_SHEET_ITEMS[accounting_standard].items() }
        fin = financial_by_period.get(period_end)

        roe = disclosed.get("roe")  # 開示優先
        equity_ratio = disclosed.get("equity_ratio") or _safe_div(bs["equity"], fin.total_assets)  # 開示優先、なければ計算
        roa = _safe_div(fin.net_profit, fin.total_assets)  # 常に計算（グループB、開示値は存在しない）
        current_ratio = _safe_div(bs["current_assets"], bs["current_liabilities"])
        ...
        RatioRecord(fiscal_year=..., period_end=..., roe=roe, equity_ratio=equity_ratio, ...)

_safe_div(numerator, denominator):
    分子・分母のいずれかがNone、または分母が0の場合はNoneを返す（FR-26のエラー方針）
```

`_safe_div`は新規のヘルパー関数。ゼロ除算・`None`同士の演算エラーを起こさないことだけを
保証する（既存の`_lookup_metric`とは別の小さな関数として`routers/companies.py`に追加する）。

### スキーマ（`backend/schemas.py`に追加）

`RatioRecord`：`docs/design/api/components/schemas/RatioRecord.yaml`の全フィールドに対応する
Pydanticモデル（`fiscal_year: str`・`period_end: date`・以下すべて`float | None`：
`roe`・`equity_ratio`・`eps`・`per`・`payout_ratio`・`roa`・`total_asset_turnover`・
`operating_margin`・`net_margin`・`current_ratio`・`fixed_ratio`・`inventory_turnover`）。

### フロントエンド設計

- `frontend/src/lib/formatRatio.ts`（新規）：`formatRatioForDisplay(value: number | null, unit: "%" | "回" | "円")`
  のような、比率・回転率・EPS用のフォーマット関数を追加する（既存の`formatYenForDisplay`は
  金額専用のため流用しない）
- `frontend/src/components/RatioSection.tsx`（新規）：SCR-003のCF表の下に追加する新セクション。
  指標ごとに表形式（CashFlowTableと同じレイアウトパターン）で表示する。グラフ化は今回のスコープに
  含めない（比率の種類が多く、単位もバラバラなためグラフより表の方が適切と判断。グラフ化したい
  場合はユーザーからの追加要望として次回検討）
- `frontend/src/api/client.ts`：`RatioRecord`型・`getCompanyRatios(code, fromYear?, toYear?)`関数を追加

### エラー・例外ケース
- 分母がデータなし・0の場合：`_safe_div`が`None`を返し、表側は「データなし」表示（既存パターン踏襲）
- US GAAP企業：`DISCLOSED_RATIOS`・`BALANCE_SHEET_ITEMS`とも`US GAAP`キーが空辞書のため、
  全指標が「データなし」になる（FR-20と同じ既知の制約として許容）

---

## 7. FR-27〜28：B/S・P/L分離、経常利益・自己資本、指標カテゴリ化

### バックエンド
- `metric_mappings.FIVE_METRICS`に`ordinary_profit`（Japan GAAPのみ）・`equity`
  （IFRS・Japan GAAP、`BALANCE_SHEET_ITEMS`からは削除し重複を解消）を追加
- `schemas.FinancialRecord`に`ordinary_profit: int | None`・`equity: int | None`を追加
- `_build_ratio_records`の`equity_ratio`・`fixed_ratio`計算は、`bs.get("equity")`ではなく
  `fin.equity`（`_build_financial_records`の結果を再利用）を参照するよう変更（実装済み・
  実データ確認済み）
- 既存API-COM-002のレスポンスにフィールドが増えるのみで、後方互換を維持する

### フロントエンド
- `frontend/src/lib/metrics.ts`：既存の`METRIC_DEFINITIONS`（5指標混在）を廃止し、
  `BS_METRIC_DEFINITIONS`（total_assets・total_liabilities・equity）と
  `PL_METRIC_DEFINITIONS`（revenue・operating_profit・ordinary_profit・net_profit）に分割する
- 既存の`FinancialChart`・`MetricSelector`は特定の`METRIC_DEFINITIONS`に依存しない
  ジェネリックな実装に変更し、B/S・P/Lそれぞれで再利用する（`MetricKey`型をジェネリック化）
- `frontend/src/lib/ratioCategories.ts`（新規）：`DISCLOSED_RATIOS`・計算指標を
  4カテゴリ（収益性・効率性・安全性・投資指標）に分類した定義を持つ
- 収益性・効率性・安全性の3カテゴリは既存の`RatioSection`と同じ単一軸グラフ＋表のパターンを
  再利用する。投資指標カテゴリのみ、EPS（円、左軸）とPER・配当性向（倍/%、右軸）の
  2軸グラフにする（Rechartsの`yAxisId`を使い分ける）
- SCR-003は「B/Sグラフ＋トグル」「P/Lグラフ＋トグル」「CFグラフ＋表（既存のまま）」
  「財務分析指標（4カテゴリ、各グラフ＋トグル＋表）」という構成になる

### エラー・例外ケース
- 経常利益：IFRS・US GAAP企業では`FIVE_METRICS`に候補が存在しないため、常に`None`
  （＝P/Lグラフのトグルで選択しても棒が描画されない）。既存の「データなし」方針を踏襲
- 投資指標2軸グラフ：3指標中1つでもデータがない期は、その系列の棒/線のみ描画しない
  （既存の`null`非描画パターンを踏襲）

---

## 検証方法

[cycle3_company_verification.md](../requirements/cycle3_company_verification.md)の10社分の
実データ（スクラッチパッドに保存済みのCSV）を使い、実装後に以下を確認する：

1. サイクル2で検証済みの3社（リクルートHD・任天堂・野村ホールディングス）が、変更前と
   同じ結果になること（NFR-07：回帰確認）
2. トヨタ自動車の売上高、大本組の全指標、良品計画のダウンロード可否・売上高が、
   変更後に正しく取得できること
3. 正興電機製作所・太陽化学・フジックス・武田薬品工業（変更前から問題なし）が、
   変更後も引き続き正しく取得できること
