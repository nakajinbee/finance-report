"""make companies accounting_standard nullable

FR-39（全上場企業マスタの一括登録）で、財務データ未取得（＝accounting_standardが
判明していない）企業も登録できるようにするため、NOT NULL制約を外す
（docs/requirements/cycle6_requirements.md FR-40）。

Revision ID: 6b364e253159
Revises: 62c510634352
Create Date: 2026-07-22 16:55:38.355025

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '6b364e253159'
down_revision: Union[str, Sequence[str], None] = '62c510634352'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.execute("ALTER TABLE companies RENAME TO companies_old")
    op.execute(
        """
        CREATE TABLE companies (
            code VARCHAR(10) PRIMARY KEY NOT NULL,
            name VARCHAR(255) NOT NULL,
            sector VARCHAR(100),
            accounting_standard VARCHAR(50)
        )
        """
    )
    op.execute("INSERT INTO companies SELECT code, name, sector, accounting_standard FROM companies_old")
    op.execute("DROP TABLE companies_old")


def downgrade() -> None:
    """Downgrade schema."""
    op.execute("ALTER TABLE companies RENAME TO companies_old")
    op.execute(
        """
        CREATE TABLE companies (
            code VARCHAR(10) PRIMARY KEY NOT NULL,
            name VARCHAR(255) NOT NULL,
            sector VARCHAR(100),
            accounting_standard VARCHAR(50) NOT NULL
        )
        """
    )
    op.execute("INSERT INTO companies SELECT code, name, sector, accounting_standard FROM companies_old")
    op.execute("DROP TABLE companies_old")
