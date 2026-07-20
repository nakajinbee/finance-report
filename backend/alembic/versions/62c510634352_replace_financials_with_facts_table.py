"""replace financials with facts table

TBL-002 financials（5指標固定カラム）を廃止し、TBL-003 facts（汎用ファクトテーブル）に
置き換える（docs/design/table/TBL-003_facts.md、docs/requirements/cycle2_requirements.md FR-05）。
既存データは移行しない（サイクル1のリクルートHDデータは破棄し、再ダウンロードする）。

Revision ID: 62c510634352
Revises: 94452a3cdebf
Create Date: 2026-07-20 17:22:41.278321

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '62c510634352'
down_revision: Union[str, Sequence[str], None] = '94452a3cdebf'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.execute("DROP TABLE financials")

    op.execute(
        """
        CREATE TABLE facts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            company_code VARCHAR(10) NOT NULL,
            doc_id VARCHAR(8) NOT NULL,
            doc_type_code VARCHAR(3) NOT NULL,
            period_end DATE NOT NULL,
            element_id VARCHAR(255) NOT NULL,
            element_name VARCHAR(255),
            context_id VARCHAR(100) NOT NULL,
            consolidated_or_individual VARCHAR(20),
            period_or_instant VARCHAR(10),
            unit VARCHAR(20),
            value NUMERIC(30, 4) NOT NULL,
            CONSTRAINT uq_company_doc_element_context UNIQUE (company_code, doc_id, element_id, context_id),
            CONSTRAINT fk_facts_company FOREIGN KEY (company_code)
                REFERENCES companies (code) ON DELETE CASCADE
        )
        """
    )

    op.execute("CREATE INDEX idx_company_element ON facts (company_code, element_id)")
    op.execute("CREATE INDEX idx_company_period ON facts (company_code, period_end)")


def downgrade() -> None:
    """Downgrade schema."""
    op.execute("DROP TABLE facts")

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
