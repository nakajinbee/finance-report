"""rename facts table and documents column for naming clarity

facts→company_quantitative_factsへのテーブル名リネーム、documents.facts_ingested_at→
body_ingested_atへのカラム名リネーム（サイクル13 FR-59）。旧名は「定量データである」
ことが名前から読み取れない曖昧な命名だったため是正する。データの中身・行数は
変更しない（名前のみの変更）。

Revision ID: 1dcd7dd744e4
Revises: 37600870423b
Create Date: 2026-07-23 23:34:47.263194

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '1dcd7dd744e4'
down_revision: Union[str, Sequence[str], None] = '37600870423b'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.execute("ALTER TABLE facts RENAME TO company_quantitative_facts")
    op.execute("ALTER TABLE documents RENAME COLUMN facts_ingested_at TO body_ingested_at")


def downgrade() -> None:
    """Downgrade schema."""
    op.execute("ALTER TABLE documents RENAME COLUMN body_ingested_at TO facts_ingested_at")
    op.execute("ALTER TABLE company_quantitative_facts RENAME TO facts")
