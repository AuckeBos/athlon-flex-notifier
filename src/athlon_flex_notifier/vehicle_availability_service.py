from logging import Logger

from athlon_flex_api import AthlonFlexApi
from athlon_flex_api.models.vehicle_cluster import DetailLevel
from kink import inject

from athlon_flex_notifier.models.vehicle_availability import VehicleAvailability
from athlon_flex_notifier.models.vehicle_cluster import VehicleCluster


@inject
class VehicleAvailabilityServices:
    """Service that upserts and deletes vehicle_availabilities.

    When ran, updates the vehicle_availabilities table. First it uses
    the AthlonFlexAPI to load all available vehicle clusters into the database.
    Then it creates new vehicle_availability reocrds for vehicles that are
    available, but do not have an activate availability.
    Finally it deletes availabilities for vehicles that are no longer available.
    """

    api: AthlonFlexApi
    logger: Logger

    @inject
    def __init__(self, api: AthlonFlexApi, logger: Logger) -> None:
        self.api = api
        self.logger = logger

    def update_availabilities(self) -> None:
        availabilities_to_deactivate = self._existing_availabilities
        available_clusters = self._currently_available_clusters
        self.logger.info(
            "%s clusters; %s vehicles;",
            len(available_clusters),
            sum(len(cluster.vehicles) for cluster in available_clusters),
        )
        for vehicle_cluster in available_clusters:
            for vehicle in vehicle_cluster.vehicles:
                if availability := vehicle.active_availability:
                    del availabilities_to_deactivate[availability.id]
                    continue
                availability = VehicleAvailability.from_vehicle(vehicle)
                self.logger.info("New vehicle is available: %s", availability)
        for availability in availabilities_to_deactivate.values():
            availability.deactivate()
            self.logger.info("Vehicle is no longer available: %s", availability)

    @property
    def _currently_available_clusters(self) -> list[VehicleCluster]:
        return [
            VehicleCluster.from_base(base)
            for base in (
                self.api.vehicle_clusters(
                    detail_level=DetailLevel.INCLUDE_VEHICLE_DETAILS
                )
            ).vehicle_clusters
        ]

    @property
    def _existing_availabilities(self) -> dict[int, VehicleAvailability]:
        return {
            availability.id: availability
            for availability in VehicleAvailability.all()
            if availability.is_currently_available
        }
