from athlon_flex_api import AthlonFlexApi
from athlon_flex_api.models.vehicle_cluster import DetailLevel, VehicleClusters
from kink import inject

from athlon_flex_notifier.models.vehicle_cluster import VehicleCluster


@inject
def main(api: AthlonFlexApi):
    response: VehicleClusters = api.vehicle_clusters(
        detail_level=DetailLevel.INCLUDE_VEHICLE_DETAILS
    )
    for base in response.vehicle_clusters:
        cluster = VehicleCluster.from_base(base)
        print(cluster)


if __name__ == "__main__":
    main()
