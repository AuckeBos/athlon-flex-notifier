from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, func
from sqlmodel import Field

from athlon_flex_notifier.models.tables.base_table import BaseTable

if TYPE_CHECKING:
    from athlon_flex_notifier.models.views.vehicle_availability import (
        VehicleAvailability,
    )


class Notification(BaseTable, table=True):
    """A notification of a vehicle becoming available."""

    vehicle_key_hash: str
    available_since: datetime = Field(
        sa_type=DateTime(timezone=True),
    )
    notified_at: datetime | None = Field(
        default=None,
        sa_type=DateTime(timezone=True),
        sa_column_kwargs={
            "onupdate": func.now(),
            "server_default": func.now(),
            "server_onupdate": func.now(),
        },
    )

    @classmethod
    def scd1_attribute_keys(cls) -> list[str]:
        return ["notified_at"]

    @staticmethod
    def business_keys() -> list[str]:
        return ["vehicle_key_hash", "available_since"]

    @classmethod
    def create_from_availability(
        cls, vehicle_availability: "VehicleAvailability"
    ) -> "Notification":
        """Create a SQLModel instance from a Vehicle."""
        return cls(
            vehicle_key_hash=vehicle_availability.vehicle_key_hash,
            available_since=vehicle_availability.available_since,
        )
