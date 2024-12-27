# noqa: INP001
"""Add index on key_hash.

Revision ID: c6d237b3de6a
Revises: e7672a631bab
Create Date: 2024-12-27 12:32:03.038215

"""

from collections.abc import Sequence

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "c6d237b3de6a"
down_revision: str | None = "e7672a631bab"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:  # noqa: D103
    op.create_index(
        op.f("ix_notification_key_hash"), "notification", ["key_hash"], unique=False
    )
    op.create_index(op.f("ix_option_key_hash"), "option", ["key_hash"], unique=False)
    op.create_index(op.f("ix_vehicle_key_hash"), "vehicle", ["key_hash"], unique=False)
    op.create_index(
        op.f("ix_vehicle_cluster_key_hash"),
        "vehicle_cluster",
        ["key_hash"],
        unique=False,
    )


def downgrade() -> None:  # noqa: D103
    op.drop_index(op.f("ix_vehicle_cluster_key_hash"), table_name="vehicle_cluster")
    op.drop_index(op.f("ix_vehicle_key_hash"), table_name="vehicle")
    op.drop_index(op.f("ix_option_key_hash"), table_name="option")
    op.drop_index(op.f("ix_notification_key_hash"), table_name="notification")
