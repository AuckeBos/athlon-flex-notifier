from logging import Logger

from kink import inject

from athlon_flex_notifier.models.vehicle_cluster import VehicleCluster
from athlon_flex_notifier.notifications.notifier import Notifier


@inject
class Notifiers:
    """Run multiple notifiers, and mark all notified."""

    notifiers: list[Notifier]
    logger: Logger

    @inject
    def __init__(self, notifiers: list[Notifier], logger: Logger) -> None:
        self.notifiers = notifiers
        self.logger = logger

    def notify(self) -> bool:
        return True
        if not self.vehicle_clusters:
            self.logger.info("No new vehicles are available.")
            return True

        if all(notifier.notify() for notifier in self.notifiers):
            self._mark_notified()
            return True
        return False

    def _mark_notified(self) -> None:
        for cluster in self.vehicle_clusters:
            for availability in cluster.unnotified_availabilities:
                availability.mark_as_notified()

    @property
    def vehicle_clusters(self) -> list[VehicleCluster]:
        if not self.notifiers:
            return []
        return self.notifiers[0].vehicle_clusters
