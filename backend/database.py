import os
from datetime import date

from dotenv import load_dotenv
from sqlalchemy import (
    BigInteger,
    Date,
    ForeignKey,
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


class Financial(Base):
    """TBL-002 financials"""

    __tablename__ = "financials"
    __table_args__ = (
        UniqueConstraint("company_code", "period_end", name="uq_company_period"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    company_code: Mapped[str] = mapped_column(
        String(10), ForeignKey("companies.code", ondelete="CASCADE"), nullable=False, index=True
    )
    period_end: Mapped[date] = mapped_column(Date, nullable=False)
    fiscal_year: Mapped[str] = mapped_column(String(20), nullable=False)
    revenue: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    operating_profit: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    net_profit: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    total_assets: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    total_liabilities: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
