import os
from datetime import date, datetime
from decimal import Decimal

from dotenv import load_dotenv
from sqlalchemy import (
    Date,
    DateTime,
    ForeignKey,
    Index,
    Numeric,
    String,
    UniqueConstraint,
    create_engine,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, sessionmaker

load_dotenv()

DATABASE_URL = os.environ["DATABASE_URL"]

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)


class Base(DeclarativeBase):
    pass


class Company(Base):
    """TBL-001 companies"""

    __tablename__ = "companies"

    code: Mapped[str] = mapped_column(String(10), primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    sector: Mapped[str | None] = mapped_column(String(100), nullable=True)
    accounting_standard: Mapped[str | None] = mapped_column(String(50), nullable=True)


class Fact(Base):
    """TBL-003 facts（TBL-002 financialsの後継、サイクル2）"""

    __tablename__ = "facts"
    __table_args__ = (
        UniqueConstraint(
            "company_code", "doc_id", "element_id", "context_id", name="uq_company_doc_element_context"
        ),
        Index("idx_company_element", "company_code", "element_id"),
        Index("idx_company_period", "company_code", "period_end"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    company_code: Mapped[str] = mapped_column(
        String(10), ForeignKey("companies.code", ondelete="CASCADE"), nullable=False
    )
    doc_id: Mapped[str] = mapped_column(String(8), nullable=False)
    doc_type_code: Mapped[str] = mapped_column(String(3), nullable=False)
    period_end: Mapped[date] = mapped_column(Date, nullable=False)
    element_id: Mapped[str] = mapped_column(String(255), nullable=False)
    element_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    context_id: Mapped[str] = mapped_column(String(100), nullable=False)
    consolidated_or_individual: Mapped[str | None] = mapped_column(String(20), nullable=True)
    period_or_instant: Mapped[str | None] = mapped_column(String(10), nullable=True)
    unit: Mapped[str | None] = mapped_column(String(20), nullable=True)
    value: Mapped[Decimal] = mapped_column(Numeric(30, 4), nullable=False)


class Document(Base):
    """TBL-004 documents（書類一覧APIのメタデータ、サイクル9）

    facts（数値データそのもの）とは別に「どの書類が存在するか」の索引を持つ。
    company_code・sec_codeを持たない書類（ファンド等）や、対象外の書類種別
    （有価証券報告書・半期報告書以外）は保存しない。
    """

    __tablename__ = "documents"
    __table_args__ = (
        Index("idx_documents_company_ingested", "company_code", "facts_ingested_at"),
        Index("idx_documents_list_date", "list_date"),
    )

    doc_id: Mapped[str] = mapped_column(String(8), primary_key=True)
    edinet_code: Mapped[str] = mapped_column(String(10), nullable=False)
    company_code: Mapped[str] = mapped_column(
        String(10), ForeignKey("companies.code", ondelete="CASCADE"), nullable=False
    )
    doc_type_code: Mapped[str] = mapped_column(String(3), nullable=False)
    period_start: Mapped[date | None] = mapped_column(Date, nullable=True)
    period_end: Mapped[date | None] = mapped_column(Date, nullable=True)
    submit_date_time: Mapped[str] = mapped_column(String(16), nullable=False)
    list_date: Mapped[date] = mapped_column(Date, nullable=False)
    withdrawal_status: Mapped[str | None] = mapped_column(String(1), nullable=True)
    disclosure_status: Mapped[str | None] = mapped_column(String(1), nullable=True)
    csv_flag: Mapped[str | None] = mapped_column(String(1), nullable=True)
    facts_ingested_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
