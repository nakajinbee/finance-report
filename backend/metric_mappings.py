"""会計基準ごとの「よく使う指標」の要素ID・コンテキストIDマッピング

TBL-003 facts は生データをそのまま保持する設計（FR-05）のため、「売上高」に対応する
element_id は会計基準によって異なる。この対応関係はクエリ時（API層、routers/companies.py）
の関心事であり、パーサー（xbrl_parser.py）はこれを知らない。

すべて実機検証済み（docs/requirements/cycle2_requirements.md FR-06・FR-13、
検証対象：リクルートHD=IFRS、任天堂=Japan GAAP、野村ホールディングス=US GAAP）。
"""

# SCR-003のグラフ5指標（売上高・営業利益・純利益・総資産・負債合計）
FIVE_METRICS: dict[str, dict[str, tuple[str, str]]] = {
    "IFRS": {
        "revenue": ("jpcrp_cor:RevenueIFRSSummaryOfBusinessResults", "CurrentYearDuration"),
        "operating_profit": ("jpigp_cor:OperatingProfitLossIFRS", "CurrentYearDuration"),
        "net_profit": (
            "jpcrp_cor:ProfitLossAttributableToOwnersOfParentIFRSSummaryOfBusinessResults",
            "CurrentYearDuration",
        ),
        "total_assets": ("jpcrp_cor:TotalAssetsIFRSSummaryOfBusinessResults", "CurrentYearInstant"),
        "total_liabilities": ("jpigp_cor:LiabilitiesIFRS", "CurrentYearInstant"),
    },
    "Japan GAAP": {
        "revenue": ("jpcrp_cor:NetSalesSummaryOfBusinessResults", "CurrentYearDuration"),
        "operating_profit": ("jppfs_cor:OperatingIncome", "CurrentYearDuration"),
        "net_profit": (
            "jpcrp_cor:ProfitLossAttributableToOwnersOfParentSummaryOfBusinessResults",
            "CurrentYearDuration",
        ),
        "total_assets": ("jpcrp_cor:TotalAssetsSummaryOfBusinessResults", "CurrentYearInstant"),
        "total_liabilities": ("jppfs_cor:Liabilities", "CurrentYearInstant"),
    },
    "US GAAP": {
        "revenue": ("jpcrp_cor:RevenuesUSGAAPSummaryOfBusinessResults", "CurrentYearDuration"),
        "net_profit": (
            "jpcrp_cor:NetIncomeLossAttributableToOwnersOfParentUSGAAPSummaryOfBusinessResults",
            "CurrentYearDuration",
        ),
        "total_assets": ("jpcrp_cor:TotalAssetsUSGAAPSummaryOfBusinessResults", "CurrentYearInstant"),
        # operating_profit・total_liabilities：野村HDでは連結ベースの要素が存在しなかった
        # （証券会社特有の開示形式のため。cycle2_requirements.md FR-06参照）。
        # マッピングが無い指標は API 側で「データなし」として扱う（FR-03）。
    },
}

# SCR-003のキャッシュフロー表（営業・投資・財務の3項目、全てCurrentYearDurationコンテキスト）
CASH_FLOW_CONTEXT_ID = "CurrentYearDuration"
CASH_FLOW: dict[str, dict[str, str]] = {
    "IFRS": {
        "operating": "jpcrp_cor:CashFlowsFromUsedInOperatingActivitiesIFRSSummaryOfBusinessResults",
        "investing": "jpcrp_cor:CashFlowsFromUsedInInvestingActivitiesIFRSSummaryOfBusinessResults",
        "financing": "jpcrp_cor:CashFlowsFromUsedInFinancingActivitiesIFRSSummaryOfBusinessResults",
    },
    "Japan GAAP": {
        "operating": "jpcrp_cor:NetCashProvidedByUsedInOperatingActivitiesSummaryOfBusinessResults",
        "investing": "jpcrp_cor:NetCashProvidedByUsedInInvestingActivitiesSummaryOfBusinessResults",
        "financing": "jpcrp_cor:NetCashProvidedByUsedInFinancingActivitiesSummaryOfBusinessResults",
    },
    "US GAAP": {
        "operating": "jpcrp_cor:CashFlowsFromUsedInOperatingActivitiesUSGAAPSummaryOfBusinessResults",
        "investing": "jpcrp_cor:CashFlowsFromUsedInInvestingActivitiesUSGAAPSummaryOfBusinessResults",
        "financing": "jpcrp_cor:CashFlowsFromUsedInFinancingActivitiesUSGAAPSummaryOfBusinessResults",
    },
}
