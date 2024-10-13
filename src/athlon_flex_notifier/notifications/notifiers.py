from dataclasses import dataclass

from athlon_flex_notifier.models.vehicle_cluster import VehicleCluster
from athlon_flex_notifier.notifications.notifier import Notifier


@dataclass
class Notifiers:
    """Run multiple notifiers, and mark all notified."""

    notifiers: list[Notifier]

    def notify(self) -> bool:
        if all(notifier.notify() for notifier in self.notifiers):
            self._mark_notified()

    def _mark_notified(self) -> None:
        for cluster in self.vehicle_clusters:
            for availability in cluster.unnotified_availabilities:
                availability.mark_as_notified()

    @property
    def vehicle_clusters(self) -> list[VehicleCluster]:
        if not self.notifiers:
            return []
        return self.notifiers[0].vehicle_clusters
