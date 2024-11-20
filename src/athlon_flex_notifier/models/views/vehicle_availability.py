from datetime import datetime
from functools import cached_property
from hashlib import sha256

from kink import di
from sqlmodel import Session, select

from athlon_flex_notifier.models.tables.base_table import BaseTable
from athlon_flex_notifier.models.tables.notification import Notification
from athlon_flex_notifier.models.tables.vehicle import Vehicle
from athlon_flex_notifier.models.views.base_view import BaseView


class VehicleAvailability(BaseView):
    """Pydantic model to hold rows in the vw_vehicle_availability view."""

    vehicle_key_hash: str
    make: str
    model: str
    available_since: datetime
    available_until: datetime | None

    @staticmethod
    def view_name() -> str:
        return "vw_vehicle_availability"

    @cached_property
    def key_hash(self) -> str:
        keys = sorted(["vehicle_key_hash", "available_since"])
        return sha256(
            BaseTable.HASH_SEPARATOR.join(
                [str(getattr(self, key)) for key in keys]
            ).encode()
        ).hexdigest()

    @cached_property
    def vehicle(self) -> Vehicle:
        """Get the vehicle for this availability."""
        with Session(di["database"]) as session:
            vehicles = list(
                session.exec(
                    select(Vehicle)
                    .where(Vehicle.key_hash == self.vehicle_key_hash)
                    .order_by(Vehicle.active_from.desc()),
                    execution_options={"include_inactive": True},
                ).unique()
            )
            if not vehicles:
                msg = f"Vehicle not found for key_hash {self.vehicle_key_hash}"
                raise ValueError(msg)
            return vehicles[0]

    @classmethod
    def to_notify(cls) -> list["VehicleAvailability"]:
        """Get all VehicleAvailability for which a notification does not yet exist."""
        yet_notified = [notification.key_hash for notification in Notification.all()]
        return [
            availability
            for availability in cls.all()
            if availability.key_hash not in yet_notified
        ]

    def __str__(self) -> str:
        return f"{self.vehicle!s} - available since {self.available_since}"
