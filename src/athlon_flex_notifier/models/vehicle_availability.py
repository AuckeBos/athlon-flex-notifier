from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import DateTime
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

    make: str
    model: str
    vehicle_id: UUID = Field(foreign_key="vehicle.id")
    vehicle_cluster_id: UUID = Field(foreign_key="vehicle_cluster.id")
    available_since: datetime | None = Field(
        sa_type=DateTime(timezone=True),
    )
    available_until: datetime | None = Field(
        sa_type=DateTime(timezone=True),
    )

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

    @staticmethod
    def business_keys() -> list[str]:
        return ["make", "model", "vehicle_id", "available_since"]

    @property
    def is_currently_available(self) -> bool:
        return self.available_until is None or now() < self.available_until.astimezone(
            timezone.utc
        )

    @classmethod
    def _from_vehicle(cls, vehicle: Vehicle) -> "VehicleAvailability":
        """Create a SQLModel instance from a Vehicle."""
        return cls(
            make=vehicle.make,
            model=vehicle.model,
            available_since=now(),
            vehicle_id=vehicle.id,
            vehicle_cluster_id=vehicle.vehicle_cluster_id,
        )

    @classmethod
    def from_vehicles(cls, *vehicles: Vehicle) -> "VehicleAvailability":
        """Create SQLModel instances for a list of vehicles, and save them in DB."""
        return cls.upsert(*[cls._from_vehicle(vehicle) for vehicle in vehicles])

    def deactivate(self) -> None:
        self.available_until = now()
        self.upsert(self)

    def mark_as_notified(self) -> None:
        self.notified = True
        self.upsert(self)

    def __str__(self) -> str:
        return f"{self.vehicle!s} - available since {self.available_since}"
