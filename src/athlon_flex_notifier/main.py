from athlon_flex_api import AthlonFlexApi
from athlon_flex_api.models.vehicle_cluster import DetailLevel, VehicleClusters
from kink import inject

from athlon_flex_notifier.models.vehicle_cluster import VehicleCluster


@inject
def main(api: AthlonFlexApi):
    response: VehicleClusters = api.vehicle_clusters(
        detail_level=DetailLevel.CLUSTER_ONLY
    )
    vehicle_clusters = [
        VehicleCluster.from_base(vehicle_cluster)
        for vehicle_cluster in response.vehicle_clusters
    ]
    # convert to document base class, and save in db
    print(vehicle_clusters)


if __name__ == "__main__":
    main()
