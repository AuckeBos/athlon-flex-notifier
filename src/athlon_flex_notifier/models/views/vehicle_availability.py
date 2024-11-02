from datetime import datetime
from functools import cached_property
from hashlib import sha256

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
        vehicles = Vehicle.get(key_hashes=[self.vehicle_key_hash])
        if len(vehicles) != 1:
            msg = f"Expected 1 vehicle, got {len(vehicles)}"
            raise ValueError(msg)
        return vehicles[0]

    @classmethod
    def to_notify(cls) -> list["VehicleAvailability"]:
        """Get all VehicleAvailability for which a notification does not yet exist."""
        active_vehicle_availabilities = [
            vehicle_availability
            for vehicle_availability in cls.all()
            if vehicle_availability.available_until is None
        ]
        notifications = Notification.all()
        yet_notified = [notification.key_hash for notification in notifications]
        return [
            availability
            for availability in active_vehicle_availabilities
            if availability.key_hash not in yet_notified
        ]

    def __str__(self) -> str:
        return f"{self.vehicle!s} - available since {self.available_since}"
