from logging import Logger

from athlon_flex_api import AthlonFlexApi
from athlon_flex_api.models.filters.vehicle_cluster_filter import AllVehicleClusters
from athlon_flex_api.models.vehicle_cluster import DetailLevel
from kink import inject

from athlon_flex_notifier.models.tables.vehicle_cluster import VehicleCluster
from athlon_flex_notifier.utils import time_it


@inject
class Refresher:
    """Service to refresh the database.

    Uses the AthlonFlexApi to load all currently available
    clusters and vehicles. from_bases will upsert the clusters and vehicles
    SCD2.
    """

    api: AthlonFlexApi
    logger: Logger

    @inject
    def __init__(self, api: AthlonFlexApi, logger: Logger) -> None:
        self.api = api
        self.logger = logger

    def refresh(self) -> None:
        self.logger.debug("Loading clusters...")
        with time_it("Loading clusters"):
            base_clusters = self.api.vehicle_clusters(
                detail_level=DetailLevel.INCLUDE_VEHICLE_DETAILS,
                filter_=AllVehicleClusters(),
            )
        with time_it("Upserting clusters"):
            VehicleCluster.store_api_response(base_clusters)
