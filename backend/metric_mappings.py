"""会計基準ごとの「よく使う指標」のマッピング（サイクル3で候補リスト方式に精緻化）

サイクル2までは「1指標=1つのelement_id（完全一致）」で固定していたが、サイクル3で
リクルートHD・任天堂・野村HD以外の企業を実機検証した結果、同じ会計基準でも企業によって
使う要素ID（タグ）が異なることが判明した（詳細は
docs/domain/xbrl_tagging_variability.md、docs/requirements/cycle3_requirements.md FR-17参照）。

そのため、要素IDは「タクソノミ名前空間を含む完全一致」ではなく、コロン以降の
**ローカル名**（例：`RevenueIFRSSummaryOfBusinessResults`）の候補リストで照合する方式に変更した。
企業固有拡張タグ（トヨタ自動車の例）でも、ローカル名は他社と似た命名規則に従うことが多いため、
候補リストに含めておけば拾える。

候補リストは優先順位付きで、実機検証済みのものだけを追加する（未検証の憶測タグは追加しない）。
コンテキストIDの非連結フォールバック（FR-18）は`routers/companies.py`の照合ロジック側で
一律に処理する（全指標・全会計基準で共通のため、ここでは扱わない）。
"""

# 指標ごとのコンテキストID種別（会計基準・企業によらず一定：金額の期間/時点の概念で決まる）
METRIC_CONTEXT_ID: dict[str, str] = {
    "revenue": "CurrentYearDuration",
    "operating_profit": "CurrentYearDuration",
    "ordinary_profit": "CurrentYearDuration",
    "net_profit": "CurrentYearDuration",
    "total_assets": "CurrentYearInstant",
    "total_liabilities": "CurrentYearInstant",
    "equity": "CurrentYearInstant",
}

# SCR-003のP/L・B/Sグラフ用の指標（売上高・営業利益・経常利益・純利益・総資産・負債・自己資本）
# 値はローカル名（要素IDのコロン以降）の候補リスト。優先順位付き
FIVE_METRICS: dict[str, dict[str, list[str]]] = {
    "IFRS": {
        "revenue": [
            "RevenueIFRSSummaryOfBusinessResults",
            # トヨタ自動車の自社拡張タグ（cycle3_company_verification.md参照）
            "OperatingRevenuesIFRSKeyFinancialData",
        ],
        "operating_profit": ["OperatingProfitLossIFRS"],
        # 経常利益はJapan GAAP特有の概念のため、IFRSには対応する候補を追加しない
        # （IFRSに「経常」区分は存在しない。常にデータなしとなる、2026-07-22ユーザー承認済み）
        "net_profit": ["ProfitLossAttributableToOwnersOfParentIFRSSummaryOfBusinessResults"],
        "total_assets": ["TotalAssetsIFRSSummaryOfBusinessResults"],
        "total_liabilities": ["LiabilitiesIFRS"],
        "equity": ["EquityIFRS"],
    },
    "Japan GAAP": {
        "revenue": [
            "NetSalesSummaryOfBusinessResults",
            # 小売・サービス業等で「売上高」ではなく「営業収益」を使う企業向け（良品計画で確認済み）
            "OperatingRevenue1SummaryOfBusinessResults",
        ],
        "operating_profit": ["OperatingIncome"],
        "ordinary_profit": ["OrdinaryIncomeLossSummaryOfBusinessResults"],
        "net_profit": [
            "ProfitLossAttributableToOwnersOfParentSummaryOfBusinessResults",
            # 連結子会社を持たない企業は「親会社株主に帰属する」概念がないため、
            # 単純な当期純利益を使う（大本組で確認済み）
            "NetIncomeLossSummaryOfBusinessResults",
        ],
        "total_assets": ["TotalAssetsSummaryOfBusinessResults"],
        "total_liabilities": ["Liabilities"],
        "equity": ["NetAssets"],
    },
    "US GAAP": {
        "revenue": ["RevenuesUSGAAPSummaryOfBusinessResults"],
        "net_profit": ["NetIncomeLossAttributableToOwnersOfParentUSGAAPSummaryOfBusinessResults"],
        "total_assets": ["TotalAssetsUSGAAPSummaryOfBusinessResults"],
        # operating_profit・total_liabilities：野村HDでは連結ベースの要素が存在しなかった
        # （証券会社特有の開示形式のため。cycle2_requirements.md FR-06参照、サイクル3では対象外＝FR-20）。
        # マッピングが無い指標は API 側で「データなし」として扱う（FR-03）。
    },
}

# SCR-003のキャッシュフロー表（営業・投資・財務の3項目、全てCurrentYearDurationコンテキスト）
CASH_FLOW_CONTEXT_ID = "CurrentYearDuration"
CASH_FLOW: dict[str, dict[str, list[str]]] = {
    "IFRS": {
        "operating": ["CashFlowsFromUsedInOperatingActivitiesIFRSSummaryOfBusinessResults"],
        "investing": ["CashFlowsFromUsedInInvestingActivitiesIFRSSummaryOfBusinessResults"],
        "financing": ["CashFlowsFromUsedInFinancingActivitiesIFRSSummaryOfBusinessResults"],
    },
    "Japan GAAP": {
        "operating": ["NetCashProvidedByUsedInOperatingActivitiesSummaryOfBusinessResults"],
        "investing": ["NetCashProvidedByUsedInInvestingActivitiesSummaryOfBusinessResults"],
        "financing": ["NetCashProvidedByUsedInFinancingActivitiesSummaryOfBusinessResults"],
    },
    "US GAAP": {
        "operating": ["CashFlowsFromUsedInOperatingActivitiesUSGAAPSummaryOfBusinessResults"],
        "investing": ["CashFlowsFromUsedInInvestingActivitiesUSGAAPSummaryOfBusinessResults"],
        "financing": ["CashFlowsFromUsedInFinancingActivitiesUSGAAPSummaryOfBusinessResults"],
    },
}

# 経営指標等サマリーが個別（非連結）ベースのみで提出される企業向けのコンテキストIDフォールバック
# サフィックス（連結子会社を持たない企業向け、FR-18。大本組で確認済み）
NON_CONSOLIDATED_CONTEXT_SUFFIX = "_NonConsolidatedMember"

# グループA：EDINET自己開示の比率指標（FR-23）。値はローカル名の候補リスト
# コンテキストIDは比率ごとに異なる（ROE・EPS・PER・配当性向は期間概念でDuration、
# 自己資本比率は貸借対照表の時点概念でInstant。2026-07-22、リクルートHD・任天堂の
# 実データで確認済み。equity_ratioをDurationで引いていたバグを発見・修正）
DISCLOSED_RATIO_CONTEXT_ID: dict[str, str] = {
    "roe": "CurrentYearDuration",
    "equity_ratio": "CurrentYearInstant",
    "eps": "CurrentYearDuration",
    "per": "CurrentYearDuration",
    "payout_ratio": "CurrentYearDuration",
}
DISCLOSED_RATIOS: dict[str, dict[str, list[str]]] = {
    "IFRS": {
        "roe": ["RateOfReturnOnEquityIFRSSummaryOfBusinessResults"],
        "equity_ratio": ["RatioOfOwnersEquityToGrossAssetsIFRSSummaryOfBusinessResults"],
        "eps": ["BasicEarningsLossPerShareIFRSSummaryOfBusinessResults"],
        "per": ["PriceEarningsRatioIFRSSummaryOfBusinessResults"],
        # 配当性向のタグは会計基準によらず共通（リクルートHDで確認済み、2026-07-22）
        "payout_ratio": ["PayoutRatioSummaryOfBusinessResults"],
    },
    "Japan GAAP": {
        "roe": ["RateOfReturnOnEquitySummaryOfBusinessResults"],
        "equity_ratio": ["EquityToAssetRatioSummaryOfBusinessResults"],
        "eps": ["BasicEarningsLossPerShareSummaryOfBusinessResults"],
        "per": ["PriceEarningsRatioSummaryOfBusinessResults"],
        "payout_ratio": ["PayoutRatioSummaryOfBusinessResults"],
    },
    # US GAAP：経営指標等サマリーにこれらの比率が開示されているか未確認のため、
    # 確認できるまでは空のままとする（FR-23、未検証のタグを憶測で追加しない方針を踏襲）
    "US GAAP": {},
}

# グループC：比率計算に必要な追加の貸借対照表項目（FR-25）。値はローカル名の候補リスト
# 自己資本（equity）はFIVE_METRICSで既に取得済みのため、ここには含めない（重複回避）
BALANCE_SHEET_CONTEXT_ID = "CurrentYearInstant"
BALANCE_SHEET_ITEMS: dict[str, dict[str, list[str]]] = {
    "IFRS": {
        "current_assets": ["CurrentAssetsIFRS"],
        "current_liabilities": ["TotalCurrentLiabilitiesIFRS"],
        "non_current_assets": ["NonCurrentAssetsIFRS"],
        "inventories": ["InventoriesCAIFRS"],
    },
    "Japan GAAP": {
        "current_assets": ["CurrentAssets"],
        "current_liabilities": ["CurrentLiabilities"],
        "non_current_assets": ["NoncurrentAssets"],
        "inventories": ["Inventories"],
    },
    # US GAAP：FR-20と同じ理由（連結ベースの内訳が経営指標等・主財務諸表とも存在しない、
    # 野村HD・オリックスで確認済み）で対象外
    "US GAAP": {},
}
