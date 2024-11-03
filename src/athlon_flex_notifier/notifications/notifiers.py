from functools import cached_property
from logging import Logger

from kink import inject

from athlon_flex_notifier.models.tables.notification import Notification
from athlon_flex_notifier.models.tables.vehicle_cluster import VehicleCluster
from athlon_flex_notifier.models.views.vehicle_availability import VehicleAvailability
from athlon_flex_notifier.notifications.console_notifier import ConsoleNotifier
from athlon_flex_notifier.notifications.email_notifier import EmailNotifier
from athlon_flex_notifier.notifications.notifier import Notifier
from athlon_flex_notifier.upserter import Upserter


@inject
class Notifiers:
    """Run multiple notifiers, and mark all notified."""

    notifiers: list[Notifier]
    logger: Logger
    upserter: Upserter

    @inject
    def __init__(self, logger: Logger, upserter: Upserter) -> None:
        self.logger = logger
        self.upserter = upserter

    def notify(self) -> bool:
        if not self.vehicle_clusters:
            self.logger.info("No new vehicles are available.")
            return True

        if all(notifier.notify() for notifier in self.notifiers):
            self._mark_notified()
            return True
        return False

    @property
    def notifiers(self) -> list[Notifier]:
        return [
            ConsoleNotifier(self.availabilities_to_notify),
            EmailNotifier(self.availabilities_to_notify),
        ]

    def _mark_notified(self) -> None:
        notifications = [
            Notification.create_from_availability(availability)
            for availability in self.availabilities_to_notify
        ]
        self.upserter.upsert(notifications)

    @cached_property
    def vehicle_clusters(self) -> list[VehicleCluster]:
        return list(
            {
                availability.vehicle.vehicle_cluster.key_hash: availability.vehicle.vehicle_cluster  # noqa: E501
                for availability in self.availabilities_to_notify
            }.values()
        )

    @cached_property
    def availabilities_to_notify(self) -> list[VehicleAvailability]:
        return VehicleAvailability.to_notify()
