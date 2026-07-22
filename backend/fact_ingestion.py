"""companies・factsテーブルへの書き込みロジック。

routers/edinet.py（個別企業のダウンロードAPI）と、サイクル9で追加した
document_body_ingestion.py（documentsテーブルの未取得書類の一括取り込み）の
両方から使う共通処理のため、どちらのモジュールにも属さない独立モジュールに切り出す
（サイクル9 FR-49/FR-50。ロジック自体はサイクル1〜2時点から変更していない）。
"""
from datetime import date

from database import Company, Fact
import xbrl_parser


def upsert_company(session, company_code: str, name: str, sector: str | None, accounting_standard: str) -> None:
    company = session.get(Company, company_code)
    if company is None:
        company = Company(code=company_code)
        session.add(company)
    company.name = name
    company.sector = sector
    company.accounting_standard = accounting_standard


def upsert_facts(
    session, company_code: str, doc_id: str, doc_type_code: str, period_end: date, facts: list[xbrl_parser.NumericFact]
) -> None:
    """CSVから抽出した数値データ(NumericFact)をすべてTBL-003 factsへ保存する（FR-04）"""
    for numeric_fact in facts:
        fact = (
            session.query(Fact)
            .filter_by(
                company_code=company_code,
                doc_id=doc_id,
                element_id=numeric_fact.element_id,
                context_id=numeric_fact.context_id,
            )
            .one_or_none()
        )
        if fact is None:
            fact = Fact(
                company_code=company_code,
                doc_id=doc_id,
                element_id=numeric_fact.element_id,
                context_id=numeric_fact.context_id,
            )
            session.add(fact)
        fact.doc_type_code = doc_type_code
        fact.period_end = period_end
        fact.element_name = numeric_fact.element_name
        fact.consolidated_or_individual = numeric_fact.consolidated_or_individual
        fact.period_or_instant = numeric_fact.period_or_instant
        fact.unit = numeric_fact.unit
        fact.value = numeric_fact.value
