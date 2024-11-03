from abc import ABC, abstractmethod
from functools import cached_property
from logging import Logger

from kink import inject

from athlon_flex_notifier.models.tables.vehicle_cluster import VehicleCluster
from athlon_flex_notifier.models.views.vehicle_availability import VehicleAvailability


class Notifier(ABC):
    """A class to notify the user of new vehicles."""

    logger: Logger
    availabilities_to_notify: list[VehicleAvailability]

    @inject
    def __init__(
        self, availabilities_to_notify: list[VehicleAvailability], logger: Logger
    ) -> None:
        self.logger = logger
        self.availabilities_to_notify = availabilities_to_notify

    @abstractmethod
    def notify(self) -> bool: ...

    @cached_property
    def vehicle_clusters(self) -> list[VehicleCluster]:
        return list(
            {
                availability.vehicle.vehicle_cluster.key_hash: availability.vehicle.vehicle_cluster  # noqa: E501
                for availability in self.availabilities_to_notify
            }.values()
        )

    def availabilities_for_cluster(
        self, vehicle_cluster: VehicleCluster
    ) -> list[VehicleAvailability]:
        return [
            availability
            for availability in self.availabilities_to_notify
            if availability.vehicle.vehicle_cluster.key_hash == vehicle_cluster.key_hash
        ]
