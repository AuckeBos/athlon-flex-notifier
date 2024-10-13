from abc import ABC, abstractmethod
from logging import Logger

from kink import inject

from athlon_flex_notifier.models.vehicle_cluster import VehicleCluster


class Notifier(ABC):
    """A class to notify the user of new vehicles."""

    logger: Logger

    @inject
    def __init__(self, logger: Logger) -> None:
        self.logger = logger

    @abstractmethod
    def notify(self) -> bool: ...

    @property
    def vehicle_clusters(self) -> list[VehicleCluster]:
        """All clusters with at least one unnotified availability."""
        return [cluster for cluster in VehicleCluster.all() if cluster.should_notify]
