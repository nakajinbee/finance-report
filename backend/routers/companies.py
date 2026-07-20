from datetime import date

from fastapi import APIRouter
from fastapi.responses import JSONResponse

import metric_mappings
import schemas
from database import Company, Fact, SessionLocal

# SCR-002（企業一覧画面）・SCR-003（企業詳細画面、docs/design/screen/配下）向けの
# API-COM-*系エンドポイント。DBのみを参照し、EDINETにはアクセスしない。
#
# TODO(cycle2): docs/design/api/paths/com/ 配下（openapi.yaml）はサイクル2向けに
# 改訂・追加済みだが、このファイルはまだ以下が未実装：
#   - API-COM-002（financials）：from_year/to_year（FR-12、年度範囲指定）に未対応
#   - API-COM-003（cashflow、SCR-003 キャッシュフロー表向け）：エンドポイント自体が未実装
#   - API-COM-004（facts、SCR-004 保存済みデータ確認画面向け）：エンドポイント自体が未実装
router = APIRouter()


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
def get_company_financials(code: str):
    """API-COM-002: 指定企業の財務データを全期分返す（SCR-003 グラフ表示。EDINETにはアクセスしない）

    TODO(cycle2 FR-12): docs/design/api/paths/com/companies_code_financials.yaml（サイクル2）は
    from_year・to_yearクエリパラメータ（年度範囲指定）を受け付ける設計だが、
    この実装は未対応で常に全期間を返す。
    """
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

        facts = session.query(Fact).filter_by(company_code=code).order_by(Fact.period_end).all()
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
