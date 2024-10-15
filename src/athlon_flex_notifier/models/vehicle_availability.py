from datetime import datetime, timezone

from sqlalchemy import ForeignKeyConstraint
from sqlmodel import Field, Relationship

from athlon_flex_notifier.models.base_model import BaseModel
from athlon_flex_notifier.models.vehicle import Vehicle
from athlon_flex_notifier.models.vehicle_cluster import VehicleCluster
from athlon_flex_notifier.utils import now


class VehicleAvailability(BaseModel, table=True):
    """A model indicating what vehicles are available.

    One Vehicle can have multiple rows in this table.
    This happens becomes available, is leased, and later becomes available again.
    """

    __tablename__ = "vehicle_availability"

    id: int | None = Field(primary_key=True, default=None)
    make: str
    model: str
    vehicle_id: str = Field(foreign_key="vehicle.id", ondelete="CASCADE")
    available_since: datetime
    available_until: datetime | None = None
    notified: bool = False
    vehicle_cluster: VehicleCluster = Relationship(
        sa_relationship_kwargs={
            "lazy": "joined",
        },
        back_populates="vehicle_availabilities",
    )
    vehicle: "Vehicle" = Relationship(
        back_populates="vehicle_availabilities",
        sa_relationship_kwargs={
            "lazy": "joined",
        },
    )
    __table_args__ = (
        ForeignKeyConstraint(
            ["make", "model"], ["vehicle_cluster.make", "vehicle_cluster.model"]
        ),
    )

    @property
    def is_currently_available(self) -> bool:
        return self.available_until is None or now() < self.available_until.astimezone(
            timezone.utc
        )

    @staticmethod
    def from_vehicle(vehicle: Vehicle) -> "VehicleAvailability":
        """Create a SQLModel instance from an API vehicle, and upsert it."""
        availability = VehicleAvailability(
            make=vehicle.make,
            model=vehicle.model,
            vehicle_id=vehicle.id,
            available_since=now(),
        ).upsert()
        availability.vehicle = vehicle
        return availability

    def deactivate(self) -> None:
        self.available_until = now()
        self.upsert()

    def mark_as_notified(self) -> None:
        self.notified = True
        self.upsert()

    def __str__(self) -> str:
        return f"{self.vehicle!s} - available since {self.available_since}"
