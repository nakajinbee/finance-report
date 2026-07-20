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


def _build_financial_records(facts: list[Fact], accounting_standard: str) -> list[schemas.FinancialRecord]:
    """企業の会計基準に応じたmetric_mappings.FIVE_METRICSを使い、factsから5指標を組み立てる"""
    element_id_to_metric_name = {
        element_id: metric_name
        for metric_name, (element_id, _context_id) in metric_mappings.FIVE_METRICS.get(accounting_standard, {}).items()
    }

    values_by_period: dict[date, dict[str, int]] = {}
    for fact in facts:
        metric_name = element_id_to_metric_name.get(fact.element_id)
        if metric_name is None:
            continue
        values_by_period.setdefault(fact.period_end, {})[metric_name] = int(fact.value)

    records = []
    for period_end in sorted(values_by_period):
        values = values_by_period[period_end]
        records.append(
            schemas.FinancialRecord(
                fiscal_year=f"{period_end.year}年{period_end.month}月期",
                period_end=period_end,
                revenue=values.get("revenue"),
                operating_profit=values.get("operating_profit"),
                net_profit=values.get("net_profit"),
                total_assets=values.get("total_assets"),
                total_liabilities=values.get("total_liabilities"),
            )
        )
    return records


def _build_cash_flow_records(facts: list[Fact], accounting_standard: str) -> list[schemas.CashFlowRecord]:
    """企業の会計基準に応じたmetric_mappings.CASH_FLOWを使い、factsから営業・投資・財務CFを組み立てる（FR-13）"""
    element_id_to_cf_name = {
        element_id: cf_name
        for cf_name, element_id in metric_mappings.CASH_FLOW.get(accounting_standard, {}).items()
    }

    values_by_period: dict[date, dict[str, int]] = {}
    for fact in facts:
        cf_name = element_id_to_cf_name.get(fact.element_id)
        if cf_name is None:
            continue
        values_by_period.setdefault(fact.period_end, {})[cf_name] = int(fact.value)

    records = []
    for period_end in sorted(values_by_period):
        values = values_by_period[period_end]
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
