"""create documents table

TBL-004 documents（書類一覧APIのメタデータ）を新設する。EDINETの書類一覧APIは日付指定で
その日の全提出書類を返す設計であり、企業を指定して取得する機能はないため、まず日付単位で
書類の存在を索引化し、後続処理（facts取り込み）が「どの書類を取ればよいか」を既知の
状態から始められるようにする（docs/requirements/cycle9_requirements.md FR-48）。

Revision ID: 37600870423b
Revises: 6b364e253159
Create Date: 2026-07-23 00:41:23.314965

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '37600870423b'
down_revision: Union[str, Sequence[str], None] = '6b364e253159'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.execute(
        """
        CREATE TABLE documents (
            doc_id VARCHAR(8) PRIMARY KEY NOT NULL,
            edinet_code VARCHAR(10) NOT NULL,
            company_code VARCHAR(10) NOT NULL,
            doc_type_code VARCHAR(3) NOT NULL,
            period_start DATE,
            period_end DATE,
            submit_date_time VARCHAR(16) NOT NULL,
            list_date DATE NOT NULL,
            withdrawal_status VARCHAR(1),
            disclosure_status VARCHAR(1),
            csv_flag VARCHAR(1),
            facts_ingested_at DATETIME,
            CONSTRAINT fk_documents_company FOREIGN KEY (company_code)
                REFERENCES companies (code) ON DELETE CASCADE
        )
        """
    )
    op.execute("CREATE INDEX idx_documents_company_ingested ON documents (company_code, facts_ingested_at)")
    op.execute("CREATE INDEX idx_documents_list_date ON documents (list_date)")


def downgrade() -> None:
    """Downgrade schema."""
    op.execute("DROP TABLE documents")
