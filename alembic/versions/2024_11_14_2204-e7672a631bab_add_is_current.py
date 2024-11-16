# noqa: INP001
"""Add is_current.

Revision ID: e7672a631bab
Revises: a491bf92b0f3
Create Date: 2024-11-14 22:04:25.665417

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "e7672a631bab"
down_revision: str | None = "a491bf92b0f3"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:  # noqa: D103
    op.add_column(
        "notification",
        sa.Column("is_current", sa.Boolean(), nullable=True, sort_order=95),
    )
    op.add_column(
        "option", sa.Column("is_current", sa.Boolean(), nullable=True, sort_order=95)
    )
    op.add_column(
        "vehicle", sa.Column("is_current", sa.Boolean(), nullable=True, sort_order=95)
    )
    op.add_column(
        "vehicle_cluster",
        sa.Column("is_current", sa.Boolean(), nullable=True, sort_order=95),
    )


def downgrade() -> None:  # noqa: D103
    op.drop_column("vehicle_cluster", "is_current")
    op.drop_column("vehicle", "is_current")
    op.drop_column("option", "is_current")
    op.drop_column("notification", "is_current")
