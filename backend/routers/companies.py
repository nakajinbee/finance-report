from fastapi import APIRouter
from fastapi.responses import JSONResponse

import schemas
from database import Company, Financial, SessionLocal

router = APIRouter()


@router.get("/companies", response_model=list[schemas.Company])
def list_companies():
    """API-COM-001: DBに保存済みの企業一覧を返す（EDINETにはアクセスしない）"""
    session = SessionLocal()
    try:
        companies = session.query(Company).order_by(Company.code).all()
        result = []
        for company in companies:
            periods = (
                session.query(Financial.period_end)
                .filter_by(company_code=company.code)
                .order_by(Financial.period_end)
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
def get_company_financials(code: str):
    """API-COM-002: 指定企業の財務データを全期分返す（EDINETにはアクセスしない）"""
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

        financials = (
            session.query(Financial)
            .filter_by(company_code=code)
            .order_by(Financial.period_end)
            .all()
        )

        return schemas.CompanyFinancials(
            company=schemas.Company(
                code=company.code,
                name=company.name,
                sector=company.sector,
                accounting_standard=company.accounting_standard,
                periods=[f.period_end for f in financials],
            ),
            data=[
                schemas.FinancialRecord(
                    fiscal_year=f.fiscal_year,
                    period_end=f.period_end,
                    revenue=f.revenue,
                    operating_profit=f.operating_profit,
                    net_profit=f.net_profit,
                    total_assets=f.total_assets,
                    total_liabilities=f.total_liabilities,
                )
                for f in financials
            ],
        )
    finally:
        session.close()
