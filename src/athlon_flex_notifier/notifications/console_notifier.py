from athlon_flex_notifier.notifications.notifier import Notifier


class ConsoleNotifier(Notifier):
    """Notify by printing to the console."""

    def notify(self) -> bool:
        self.logger.info("The following new vehicles are available:")
        for vehicle_cluster in self.vehicle_clusters:
            self.logger.info("\t %s", vehicle_cluster)
            for availability in vehicle_cluster.unnotified_availabilities:
                self.logger.info("\t\t %s", availability)
        return True
