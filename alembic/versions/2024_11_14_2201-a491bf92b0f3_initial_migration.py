# noqa: INP001
"""Initial Migration.

Revision ID: a491bf92b0f3
Revises: Creates the initial database.
Create Date: 2024-11-14 22:01:53.469813

"""

from collections.abc import Sequence

import sqlalchemy as sa
import sqlmodel

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "a491bf92b0f3"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:  # noqa: D103
    op.create_table(
        "notification",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column(
            "key_hash", sqlmodel.sql.sqltypes.AutoString(), nullable=True, sort_order=90
        ),
        sa.Column(
            "attribute_hash_scd1",
            sqlmodel.sql.sqltypes.AutoString(),
            nullable=True,
            sort_order=91,
        ),
        sa.Column(
            "attribute_hash_scd2",
            sqlmodel.sql.sqltypes.AutoString(),
            nullable=True,
            sort_order=92,
        ),
        sa.Column(
            "active_from", sa.DateTime(timezone=True), nullable=False, sort_order=93
        ),
        sa.Column(
            "active_to", sa.DateTime(timezone=True), nullable=True, sort_order=94
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=True,
            sort_order=96,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=True,
            sort_order=97,
        ),
        sa.Column(
            "vehicle_key_hash", sqlmodel.sql.sqltypes.AutoString(), nullable=False
        ),
        sa.Column("available_since", sa.DateTime(timezone=True), nullable=False),
        sa.Column(
            "notified_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=True,
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "vehicle_cluster",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column(
            "key_hash", sqlmodel.sql.sqltypes.AutoString(), nullable=True, sort_order=90
        ),
        sa.Column(
            "attribute_hash_scd1",
            sqlmodel.sql.sqltypes.AutoString(),
            nullable=True,
            sort_order=91,
        ),
        sa.Column(
            "attribute_hash_scd2",
            sqlmodel.sql.sqltypes.AutoString(),
            nullable=True,
            sort_order=92,
        ),
        sa.Column(
            "active_from", sa.DateTime(timezone=True), nullable=False, sort_order=93
        ),
        sa.Column(
            "active_to", sa.DateTime(timezone=True), nullable=True, sort_order=94
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=True,
            sort_order=96,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=True,
            sort_order=97,
        ),
        sa.Column(
            "first_vehicle_id", sqlmodel.sql.sqltypes.AutoString(), nullable=False
        ),
        sa.Column(
            "external_type_id", sqlmodel.sql.sqltypes.AutoString(), nullable=False
        ),
        sa.Column("make", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column("model", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column("latest_model_year", sa.Integer(), nullable=False),
        sa.Column("vehicle_count", sa.Integer(), nullable=False),
        sa.Column("min_price_in_euro_per_month", sa.Float(), nullable=False),
        sa.Column("fiscal_value_in_euro", sa.Float(), nullable=False),
        sa.Column("addition_percentage", sa.Float(), nullable=False),
        sa.Column("external_fuel_type_id", sa.Integer(), nullable=False),
        sa.Column("max_co2_emission", sa.Integer(), nullable=False),
        sa.Column("image_uri", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "vehicle",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column(
            "key_hash", sqlmodel.sql.sqltypes.AutoString(), nullable=True, sort_order=90
        ),
        sa.Column(
            "attribute_hash_scd1",
            sqlmodel.sql.sqltypes.AutoString(),
            nullable=True,
            sort_order=91,
        ),
        sa.Column(
            "attribute_hash_scd2",
            sqlmodel.sql.sqltypes.AutoString(),
            nullable=True,
            sort_order=92,
        ),
        sa.Column(
            "active_from", sa.DateTime(timezone=True), nullable=False, sort_order=93
        ),
        sa.Column(
            "active_to", sa.DateTime(timezone=True), nullable=True, sort_order=94
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=True,
            sort_order=96,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=True,
            sort_order=97,
        ),
        sa.Column("athlon_id", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column("make", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column("model", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column("type", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column("model_year", sa.Integer(), nullable=False),
        sa.Column("paint_id", sqlmodel.sql.sqltypes.AutoString(), nullable=True),
        sa.Column(
            "external_paint_id", sqlmodel.sql.sqltypes.AutoString(), nullable=True
        ),
        sa.Column("addition_percentage", sa.Float(), nullable=True),
        sa.Column("range_in_km", sa.Integer(), nullable=False),
        sa.Column("external_fuel_type_id", sa.Integer(), nullable=False),
        sa.Column(
            "external_type_id", sqlmodel.sql.sqltypes.AutoString(), nullable=False
        ),
        sa.Column("image_uri", sqlmodel.sql.sqltypes.AutoString(), nullable=True),
        sa.Column("is_electric", sa.Boolean(), nullable=True),
        sa.Column("uri", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column("license_plate", sqlmodel.sql.sqltypes.AutoString(), nullable=True),
        sa.Column("color", sqlmodel.sql.sqltypes.AutoString(), nullable=True),
        sa.Column("official_color", sqlmodel.sql.sqltypes.AutoString(), nullable=True),
        sa.Column("body_type", sqlmodel.sql.sqltypes.AutoString(), nullable=True),
        sa.Column("emission", sa.Float(), nullable=True),
        sa.Column(
            "registration_date", sqlmodel.sql.sqltypes.AutoString(), nullable=True
        ),
        sa.Column("registered_mileage", sa.Float(), nullable=True),
        sa.Column(
            "transmission_type", sqlmodel.sql.sqltypes.AutoString(), nullable=True
        ),
        sa.Column("avg_fuel_consumption", sa.Float(), nullable=True),
        sa.Column(
            "type_spare_wheel", sqlmodel.sql.sqltypes.AutoString(), nullable=True
        ),
        sa.Column("fiscal_value_in_euro", sa.Float(), nullable=True),
        sa.Column("base_price_in_euro_per_month", sa.Float(), nullable=True),
        sa.Column("calculated_price_in_euro_per_month", sa.Float(), nullable=True),
        sa.Column("price_per_km", sa.Float(), nullable=True),
        sa.Column("fuel_price_per_km", sa.Float(), nullable=True),
        sa.Column("contribution_in_euro", sa.Float(), nullable=True),
        sa.Column("expected_fuel_cost_in_euro_per_month", sa.Float(), nullable=True),
        sa.Column("net_cost_in_euro_per_month", sa.Float(), nullable=True),
        sa.Column("vehicle_cluster_id", sa.Uuid(), nullable=False),
        sa.ForeignKeyConstraint(
            ["vehicle_cluster_id"],
            ["vehicle_cluster.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "option",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column(
            "key_hash", sqlmodel.sql.sqltypes.AutoString(), nullable=True, sort_order=90
        ),
        sa.Column(
            "attribute_hash_scd1",
            sqlmodel.sql.sqltypes.AutoString(),
            nullable=True,
            sort_order=91,
        ),
        sa.Column(
            "attribute_hash_scd2",
            sqlmodel.sql.sqltypes.AutoString(),
            nullable=True,
            sort_order=92,
        ),
        sa.Column(
            "active_from", sa.DateTime(timezone=True), nullable=False, sort_order=93
        ),
        sa.Column(
            "active_to", sa.DateTime(timezone=True), nullable=True, sort_order=94
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=True,
            sort_order=96,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=True,
            sort_order=97,
        ),
        sa.Column("athlon_id", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column("externalId", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column("optionName", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column("included", sa.Boolean(), nullable=False),
        sa.Column("vehicle_id", sa.Uuid(), nullable=False),
        sa.ForeignKeyConstraint(
            ["vehicle_id"],
            ["vehicle.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )


def downgrade() -> None:  # noqa: D103
    op.drop_table("option")
    op.drop_table("vehicle")
    op.drop_table("vehicle_cluster")
    op.drop_table("notification")
