from logging import Logger

from athlon_flex_api import AthlonFlexApi
from athlon_flex_api.models.filters.vehicle_cluster_filter import AllVehicleClusters
from athlon_flex_api.models.vehicle_cluster import DetailLevel
from kink import inject

from athlon_flex_notifier.models.vehicle_availability import VehicleAvailability
from athlon_flex_notifier.models.vehicle_cluster import VehicleCluster
from athlon_flex_notifier.utils import time_it


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
        create_availabilities_for = []
        for vehicle_cluster in self._currently_available_clusters:
            for vehicle in vehicle_cluster.vehicles:
                if availability := vehicle.active_availability:
                    del availabilities_to_deactivate[availability.key_hash]
                    continue
                create_availabilities_for.append(vehicle)
        VehicleAvailability.from_vehicles(*create_availabilities_for)
        for availability in availabilities_to_deactivate.values():
            availability.deactivate()
            self.logger.info("Vehicle is no longer available: %s", availability)

    @property
    def _currently_available_clusters(self) -> list[VehicleCluster]:
        self.logger.debug("Loading clusters...")
        with time_it("Loading clusters"):
            base_clusters = (
                self.api.vehicle_clusters(
                    detail_level=DetailLevel.INCLUDE_VEHICLE_DETAILS,
                    filter_=AllVehicleClusters(),
                )
            ).vehicle_clusters
        with time_it("Upserting clusters"):
            clusters = VehicleCluster.from_base(*base_clusters[:1])
        self.logger.info(
            "Found %s clusters; %s vehicles;",
            len(base_clusters),
            sum(len(cluster.vehicles) for cluster in base_clusters),
        )
        return clusters

    @property
    def _existing_availabilities(self) -> dict[int, VehicleAvailability]:
        return {
            availability.key_hash: availability
            for availability in VehicleAvailability.all()
            if availability.is_currently_available
        }
