"""create company_qualitative_facts table

TBL-005 company_qualitative_facts（企業の定性データ）を新設する。EDINETの提出本文書
CSVに含まれる事業の内容・事業等のリスク・MD&Aのテキストブロックを保持する
（docs/requirements/cycle13_requirements.md FR-58）。

Revision ID: 25652cfde874
Revises: 1dcd7dd744e4
Create Date: 2026-07-23 23:39:09.188487

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '25652cfde874'
down_revision: Union[str, Sequence[str], None] = '1dcd7dd744e4'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.execute(
        """
        CREATE TABLE company_qualitative_facts (
            doc_id VARCHAR(8) NOT NULL,
            element_id VARCHAR(100) NOT NULL,
            company_code VARCHAR(10) NOT NULL,
            period_end DATE,
            content TEXT NOT NULL,
            PRIMARY KEY (doc_id, element_id),
            CONSTRAINT fk_company_qualitative_facts_document FOREIGN KEY (doc_id)
                REFERENCES documents (doc_id) ON DELETE CASCADE,
            CONSTRAINT fk_company_qualitative_facts_company FOREIGN KEY (company_code)
                REFERENCES companies (code) ON DELETE CASCADE
        )
        """
    )
    op.execute(
        "CREATE INDEX idx_company_qualitative_facts_company_period "
        "ON company_qualitative_facts (company_code, period_end)"
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.execute("DROP TABLE company_qualitative_facts")
