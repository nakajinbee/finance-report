from datetime import date

from fastapi import APIRouter
from fastapi.responses import JSONResponse

import edinet_client
import metric_mappings
import schemas
from database import Company, Fact, SessionLocal

# SCR-002（企業一覧画面）・SCR-003（企業詳細画面）・SCR-004（保存済みデータ確認画面、
# docs/design/screen/配下）向けのAPI-COM-*系エンドポイント。DBのみを参照し、EDINETには
# アクセスしない。
router = APIRouter()


def _validate_year_range(from_year: int | None, to_year: int | None) -> schemas.ErrorResponse | None:
    if from_year is not None and to_year is not None and from_year > to_year:
        return schemas.ErrorResponse(
            error="INVALID_PERIOD", message="from_yearはto_year以前である必要があります"
        )
    return None


def _filter_by_year_range(facts: list[Fact], from_year: int | None, to_year: int | None) -> list[Fact]:
    return [
        fact
        for fact in facts
        if (from_year is None or fact.period_end.year >= from_year)
        and (to_year is None or fact.period_end.year <= to_year)
    ]


def _local_name(element_id: str) -> str:
    """要素IDのコロン以降のローカル名を返す（企業固有拡張タグの名前空間部分を除く、FR-17）"""
    return element_id.split(":")[-1]


def _index_facts_by_period(facts: list[Fact]) -> dict[date, dict[tuple[str, str], float]]:
    """factsを期間ごとに(ローカル名, コンテキストID)→値の辞書へ変換する（FR-17）

    値はfloatのまま保持し、整数への丸めは呼び出し元（金額を扱う_build_financial_records等）
    の責務とする。ROE・EPS等の比率指標は1未満の小数を取りうるため、ここでint化すると
    精度が失われる（サイクル3 FR-23〜26の実装時に発見・修正）。
    """
    index: dict[date, dict[tuple[str, str], float]] = {}
    for fact in facts:
        index.setdefault(fact.period_end, {})[(_local_name(fact.element_id), fact.context_id)] = float(fact.value)
    return index


def _lookup_metric(period_index: dict[tuple[str, str], float], candidates: list[str], context_id: str) -> float | None:
    """候補ローカル名を優先順に探し、最初に一致した値を返す（FR-17）

    連結子会社を持たない企業は経営指標等サマリーが個別ベースのみで提出され、
    コンテキストIDにNON_CONSOLIDATED_CONTEXT_SUFFIXが付くため、そちらもフォールバックで試す
    （FR-18。連結・非連結の判別はコンテキストIDのサフィックスで行い、facts.consolidated_or_individual
    列は使わない。この列は実データ上値が一定せず判別に使えないことを確認済み
    ＝docs/design/cycle3_design.md参照）。
    """
    for local_name in candidates:
        for ctx in (context_id, context_id + metric_mappings.NON_CONSOLIDATED_CONTEXT_SUFFIX):
            value = period_index.get((local_name, ctx))
            if value is not None:
                return value
    return None


def _build_financial_records(facts: list[Fact], accounting_standard: str) -> list[schemas.FinancialRecord]:
    """企業の会計基準に応じたmetric_mappings.FIVE_METRICSを使い、factsから5指標を組み立てる"""
    metric_candidates = metric_mappings.FIVE_METRICS.get(accounting_standard, {})
    period_index = _index_facts_by_period(facts)

    records = []
    for period_end in sorted(period_index):
        values = {
            metric_name: _lookup_metric(
                period_index[period_end], candidates, metric_mappings.METRIC_CONTEXT_ID[metric_name]
            )
            for metric_name, candidates in metric_candidates.items()
        }
        if not any(value is not None for value in values.values()):
            continue
        records.append(
            schemas.FinancialRecord(
                fiscal_year=f"{period_end.year}年{period_end.month}月期",
                period_end=period_end,
                revenue=values.get("revenue"),
                operating_profit=values.get("operating_profit"),
                ordinary_profit=values.get("ordinary_profit"),
                net_profit=values.get("net_profit"),
                total_assets=values.get("total_assets"),
                total_liabilities=values.get("total_liabilities"),
                equity=values.get("equity"),
            )
        )
    return records


def _build_cash_flow_records(facts: list[Fact], accounting_standard: str) -> list[schemas.CashFlowRecord]:
    """企業の会計基準に応じたmetric_mappings.CASH_FLOWを使い、factsから営業・投資・財務CFを組み立てる（FR-13）"""
    cf_candidates = metric_mappings.CASH_FLOW.get(accounting_standard, {})
    period_index = _index_facts_by_period(facts)

    records = []
    for period_end in sorted(period_index):
        values = {
            cf_name: _lookup_metric(period_index[period_end], candidates, metric_mappings.CASH_FLOW_CONTEXT_ID)
            for cf_name, candidates in cf_candidates.items()
        }
        if not any(value is not None for value in values.values()):
            continue
        records.append(
            schemas.CashFlowRecord(
                fiscal_year=f"{period_end.year}年{period_end.month}月期",
                period_end=period_end,
                operating_cash_flow=values.get("operating"),
                investing_cash_flow=values.get("investing"),
                financing_cash_flow=values.get("financing"),
            )
        )
    return records


def _safe_div(numerator: int | float | None, denominator: int | float | None) -> float | None:
    """分子・分母のいずれかがNone、または分母が0の場合はNoneを返す（FR-26のエラー方針）"""
    if numerator is None or denominator is None or denominator == 0:
        return None
    return numerator / denominator


def _build_ratio_records(facts: list[Fact], accounting_standard: str) -> list[schemas.RatioRecord]:
    """metric_mappings.DISCLOSED_RATIOS・BALANCE_SHEET_ITEMSを使い、財務分析指標を組み立てる

    ROE・自己資本比率等はEDINET開示値を優先し、開示されていない指標のみ既存5指標・
    貸借対照表項目から計算する（FR-23〜26、ユーザー承認済みの優先順位）。
    """
    disclosed_candidates = metric_mappings.DISCLOSED_RATIOS.get(accounting_standard, {})
    balance_sheet_candidates = metric_mappings.BALANCE_SHEET_ITEMS.get(accounting_standard, {})
    period_index = _index_facts_by_period(facts)
    financial_by_period = {r.period_end: r for r in _build_financial_records(facts, accounting_standard)}

    records = []
    for period_end in sorted(period_index):
        fin = financial_by_period.get(period_end)
        if fin is None:
            continue

        disclosed = {
            ratio_name: _lookup_metric(
                period_index[period_end], candidates, metric_mappings.DISCLOSED_RATIO_CONTEXT_ID[ratio_name]
            )
            for ratio_name, candidates in disclosed_candidates.items()
        }
        bs = {
            item_name: _lookup_metric(period_index[period_end], candidates, metric_mappings.BALANCE_SHEET_CONTEXT_ID)
            for item_name, candidates in balance_sheet_candidates.items()
        }

        equity_ratio = disclosed.get("equity_ratio")
        if equity_ratio is None:
            equity_ratio = _safe_div(fin.equity, fin.total_assets)

        values = {
            "roe": disclosed.get("roe"),
            "equity_ratio": equity_ratio,
            "eps": disclosed.get("eps"),
            "per": disclosed.get("per"),
            "payout_ratio": disclosed.get("payout_ratio"),
            "roa": _safe_div(fin.net_profit, fin.total_assets),
            "total_asset_turnover": _safe_div(fin.revenue, fin.total_assets),
            "operating_margin": _safe_div(fin.operating_profit, fin.revenue),
            "net_margin": _safe_div(fin.net_profit, fin.revenue),
            "current_ratio": _safe_div(bs.get("current_assets"), bs.get("current_liabilities")),
            "fixed_ratio": _safe_div(bs.get("non_current_assets"), fin.equity),
            "inventory_turnover": _safe_div(fin.revenue, bs.get("inventories")),
            # 指標計算の元になった生の金額（ユーザー要望、2026-07-22）
            "current_assets": bs.get("current_assets"),
            "current_liabilities": bs.get("current_liabilities"),
            "non_current_assets": bs.get("non_current_assets"),
            "non_current_liabilities": bs.get("non_current_liabilities"),
            "inventories": bs.get("inventories"),
        }
        if not any(value is not None for value in values.values()):
            continue
        records.append(
            schemas.RatioRecord(
                fiscal_year=fin.fiscal_year,
                period_end=period_end,
                **values,
            )
        )
    return records


@router.get("/companies", response_model=list[schemas.Company])
def list_companies():
    """API-COM-001: DBに保存済みの企業一覧を返す（EDINETにはアクセスしない）"""
    session = SessionLocal()
    try:
        companies = session.query(Company).order_by(Company.code).all()
        result = []
        for company in companies:
            periods = (
                session.query(Fact.period_end)
                .filter_by(company_code=company.code)
                .distinct()
                .order_by(Fact.period_end)
                .all()
            )
            result.append(
                schemas.Company(
                    code=company.code,
                    name=company.name,
                    sector=company.sector,
                    accounting_standard=company.accounting_standard,
                    periods=[period_end for (period_end,) in periods],
                )
            )
        return result
    finally:
        session.close()


@router.get("/companies/{code}/financials", response_model=schemas.CompanyFinancials)
def get_company_financials(code: str, from_year: int | None = None, to_year: int | None = None):
    """API-COM-002: 指定企業の財務データを返す（SCR-003 グラフ表示。EDINETにはアクセスしない）

    from_year・to_year（FR-12）が未指定の場合はDBに保存済みの全期間を返す。
    """
    error = _validate_year_range(from_year, to_year)
    if error is not None:
        return JSONResponse(status_code=400, content=error.model_dump())

    session = SessionLocal()
    try:
        company = session.get(Company, code)
        if company is None:
            return JSONResponse(
                status_code=404,
                content=schemas.ErrorResponse(
                    error="COMPANY_NOT_FOUND", message="指定した企業が存在しません"
                ).model_dump(),
            )

        facts = (
            session.query(Fact)
            .filter_by(company_code=code, doc_type_code=edinet_client.DOC_TYPE_CODE_ANNUAL_REPORT)
            .order_by(Fact.period_end)
            .all()
        )
        facts = _filter_by_year_range(facts, from_year, to_year)
        records = _build_financial_records(facts, company.accounting_standard)

        return schemas.CompanyFinancials(
            company=schemas.Company(
                code=company.code,
                name=company.name,
                sector=company.sector,
                accounting_standard=company.accounting_standard,
                periods=[r.period_end for r in records],
            ),
            data=records,
        )
    finally:
        session.close()


@router.get("/companies/{code}/cashflow", response_model=list[schemas.CashFlowRecord])
def get_company_cash_flow(code: str, from_year: int | None = None, to_year: int | None = None):
    """API-COM-003: 指定企業の営業・投資・財務キャッシュフローを返す（SCR-003 CF表、FR-13）"""
    error = _validate_year_range(from_year, to_year)
    if error is not None:
        return JSONResponse(status_code=400, content=error.model_dump())

    session = SessionLocal()
    try:
        company = session.get(Company, code)
        if company is None:
            return JSONResponse(
                status_code=404,
                content=schemas.ErrorResponse(
                    error="COMPANY_NOT_FOUND", message="指定した企業が存在しません"
                ).model_dump(),
            )

        facts = (
            session.query(Fact)
            .filter_by(company_code=code, doc_type_code=edinet_client.DOC_TYPE_CODE_ANNUAL_REPORT)
            .order_by(Fact.period_end)
            .all()
        )
        facts = _filter_by_year_range(facts, from_year, to_year)
        return _build_cash_flow_records(facts, company.accounting_standard)
    finally:
        session.close()


@router.get("/companies/{code}/ratios", response_model=list[schemas.RatioRecord])
def get_company_ratios(code: str, from_year: int | None = None, to_year: int | None = None):
    """API-COM-005: 指定企業の財務分析指標（ROE・流動比率等）を返す（SCR-003、FR-23〜26）"""
    error = _validate_year_range(from_year, to_year)
    if error is not None:
        return JSONResponse(status_code=400, content=error.model_dump())

    session = SessionLocal()
    try:
        company = session.get(Company, code)
        if company is None:
            return JSONResponse(
                status_code=404,
                content=schemas.ErrorResponse(
                    error="COMPANY_NOT_FOUND", message="指定した企業が存在しません"
                ).model_dump(),
            )

        facts = (
            session.query(Fact)
            .filter_by(company_code=code, doc_type_code=edinet_client.DOC_TYPE_CODE_ANNUAL_REPORT)
            .order_by(Fact.period_end)
            .all()
        )
        facts = _filter_by_year_range(facts, from_year, to_year)
        return _build_ratio_records(facts, company.accounting_standard)
    finally:
        session.close()


@router.get("/companies/{code}/facts", response_model=list[schemas.FactRecord])
def get_company_facts(code: str, element_id: str | None = None, period_end: date | None = None):
    """API-COM-004: 指定企業のTBL-003 facts生データを一覧で返す（SCR-004、FR-16）"""
    session = SessionLocal()
    try:
        company = session.get(Company, code)
        if company is None:
            return JSONResponse(
                status_code=404,
                content=schemas.ErrorResponse(
                    error="COMPANY_NOT_FOUND", message="指定した企業が存在しません"
                ).model_dump(),
            )

        query = session.query(Fact).filter_by(company_code=code)
        if element_id is not None:
            query = query.filter(Fact.element_id.contains(element_id))
        if period_end is not None:
            query = query.filter_by(period_end=period_end)
        facts = query.order_by(Fact.period_end.desc(), Fact.element_id.asc()).all()

        return [
            schemas.FactRecord(
                element_id=fact.element_id,
                element_name=fact.element_name,
                doc_type_code=fact.doc_type_code,
                period_end=fact.period_end,
                context_id=fact.context_id,
                consolidated_or_individual=fact.consolidated_or_individual,
                unit=fact.unit,
                value=float(fact.value),
            )
            for fact in facts
        ]
    finally:
        session.close()
