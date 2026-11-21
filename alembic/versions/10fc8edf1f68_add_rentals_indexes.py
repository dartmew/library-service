"""add rentals indexes

Revision ID: 10fc8edf1f68
Revises: 02e0a171a148
Create Date: 2026-11-21 16:46:19.393476

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy import text


# revision identifiers, used by Alembic.
revision: str = '10fc8edf1f68'
down_revision: Union[str, Sequence[str], None] = '02e0a171a148'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_index("ix_rentals_book_id_active", "rentals", ["book_id"], postgresql_where=text("returned_at IS NULL"))
    op.create_index("ix_rentals_user_id", "rentals", ["user_id"])
    op.create_index("ix_rentals_due_check", "rentals", ["due_at"], postgresql_where=text("returned_at IS NULL"))


def downgrade() -> None:
    op.drop_index("ix_rentals_due_check", table_name="rentals")
    op.drop_index("ix_rentals_user_id", table_name="rentals")
    op.drop_index("ix_rentals_book_id_active", table_name="rentals")
