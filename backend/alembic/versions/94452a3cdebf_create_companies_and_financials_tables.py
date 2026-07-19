"""create companies and financials tables

TBL-001 companies / TBL-002 financials (docs/design/table/) のDDLをそのまま記述する。
SQLite向けのDDL。MySQL移行時は別マイグレーションとしてDDLを書き直す想定
（docs/development/backend_implementation_policy.md 参照）。

Revision ID: 94452a3cdebf
Revises:
Create Date: 2026-07-19 23:52:31.141395

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '94452a3cdebf'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
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

    op.execute(
        """
        CREATE TABLE financials (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            company_code VARCHAR(10) NOT NULL,
            period_end DATE NOT NULL,
            fiscal_year VARCHAR(20) NOT NULL,
            revenue BIGINT,
            operating_profit BIGINT,
            net_profit BIGINT,
            total_assets BIGINT,
            total_liabilities BIGINT,
            CONSTRAINT uq_company_period UNIQUE (company_code, period_end),
            CONSTRAINT fk_financials_company FOREIGN KEY (company_code)
                REFERENCES companies (code) ON DELETE CASCADE
        )
        """
    )

    op.execute("CREATE INDEX idx_company_code ON financials (company_code)")


def downgrade() -> None:
    """Downgrade schema."""
    op.execute("DROP TABLE financials")
    op.execute("DROP TABLE companies")
