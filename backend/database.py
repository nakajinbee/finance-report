import os
from datetime import date
from decimal import Decimal

from dotenv import load_dotenv
from sqlalchemy import (
    Date,
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
    accounting_standard: Mapped[str] = mapped_column(String(50), nullable=False)


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
