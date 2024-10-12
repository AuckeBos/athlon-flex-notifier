from abc import ABC, abstractmethod
from logging import Logger
from typing import TYPE_CHECKING

from kink import inject

from athlon_flex_notifier.models.vehicle_cluster import VehicleCluster

if TYPE_CHECKING:
    from athlon_flex_notifier.models.vehicle_availability import VehicleAvailability


class Notifier(ABC):
    logger: Logger

    @inject
    def __init__(self, logger: Logger) -> None:
        self.logger = logger

    @abstractmethod
    def notify(self) -> bool: ...

    @property
    def vehicle_clusters(self) -> list[VehicleCluster]:
        return [cluster for cluster in VehicleCluster.all() if cluster.should_notify]

    def mark_as_notified(self, subject: "VehicleAvailability") -> None:
        subject.mark_as_notified()
