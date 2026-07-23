"""companies・company_quantitative_facts・company_qualitative_factsテーブルへの
書き込みロジック。

routers/edinet.py（個別企業のダウンロードAPI）と、サイクル9で追加した
document_body_ingestion.py（documentsテーブルの未取得書類の一括取り込み）の
両方から使う共通処理のため、どちらのモジュールにも属さない独立モジュールに切り出す
（サイクル9 FR-49/FR-50。ロジック自体はサイクル1〜2時点から変更していない）。

サイクル13で`fact_ingestion.py`からリネーム（FR-59）、`upsert_qualitative_facts`を
追加（FR-58）。
"""
from datetime import date

from database import Company, CompanyQualitativeFact, CompanyQuantitativeFact
import xbrl_parser


def upsert_company(session, company_code: str, name: str, sector: str | None, accounting_standard: str) -> None:
    company = session.get(Company, company_code)
    if company is None:
        company = Company(code=company_code)
        session.add(company)
    company.name = name
    company.sector = sector
    company.accounting_standard = accounting_standard


def upsert_quantitative_facts(
    session,
    company_code: str,
    doc_id: str,
    doc_type_code: str,
    period_end: date,
    quantitative_facts: list[xbrl_parser.QuantitativeFact],
) -> None:
    """CSVから抽出した数値データ(QuantitativeFact)をすべてcompany_quantitative_factsへ保存する（FR-04）"""
    for quantitative_fact in quantitative_facts:
        record = (
            session.query(CompanyQuantitativeFact)
            .filter_by(
                company_code=company_code,
                doc_id=doc_id,
                element_id=quantitative_fact.element_id,
                context_id=quantitative_fact.context_id,
            )
            .one_or_none()
        )
        if record is None:
            record = CompanyQuantitativeFact(
                company_code=company_code,
                doc_id=doc_id,
                element_id=quantitative_fact.element_id,
                context_id=quantitative_fact.context_id,
            )
            session.add(record)
        record.doc_type_code = doc_type_code
        record.period_end = period_end
        record.element_name = quantitative_fact.element_name
        record.consolidated_or_individual = quantitative_fact.consolidated_or_individual
        record.period_or_instant = quantitative_fact.period_or_instant
        record.unit = quantitative_fact.unit
        record.value = quantitative_fact.value


def upsert_qualitative_facts(
    session,
    company_code: str,
    doc_id: str,
    period_end: date | None,
    qualitative_facts: list[xbrl_parser.QualitativeFact],
) -> None:
    """CSVから抽出した定性データ(QualitativeFact)をすべてcompany_qualitative_factsへ保存する（サイクル13 FR-58）"""
    for qualitative_fact in qualitative_facts:
        record = session.get(CompanyQualitativeFact, (doc_id, qualitative_fact.element_id))
        if record is None:
            record = CompanyQualitativeFact(doc_id=doc_id, element_id=qualitative_fact.element_id)
            session.add(record)
        record.company_code = company_code
        record.period_end = period_end
        record.content = qualitative_fact.content
