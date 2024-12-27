from logging import Logger

from athlon_flex_client import AthlonFlexClient
from athlon_flex_client.models.filters.vehicle_cluster_filter import AllVehicleClusters
from athlon_flex_client.models.vehicle_cluster import DetailLevel
from kink import inject

from athlon_flex_notifier.models.tables.vehicle_cluster import VehicleCluster
from athlon_flex_notifier.utils import time_it


@inject
class Refresher:
    """Service to refresh the database.

    Uses the AthlonFlexClient to load all currently available
    clusters and vehicles. from_bases will upsert the clusters and vehicles
    SCD2.
    """

    client: AthlonFlexClient
    logger: Logger

    @inject
    def __init__(self, client: AthlonFlexClient, logger: Logger) -> None:
        self.client = client
        self.logger = logger

    def refresh(self) -> None:
        self.logger.debug("Loading clusters...")
        with time_it("Loading clusters"):
            base_clusters = self.client.vehicle_clusters(
                detail_level=DetailLevel.INCLUDE_VEHICLE_DETAILS,
                filter_=AllVehicleClusters(),
            )
        VehicleCluster.store_api_response(base_clusters)
