from athlon_flex_api import AthlonFlexApi
from athlon_flex_api.models.vehicle_cluster import DetailLevel
from kink import inject

# Force bootstrap
from athlon_flex_notifier import *


@inject
def main(api: AthlonFlexApi):
    vehicle_clusters = api.vehicle_clusters(detail_level=DetailLevel.CLUSTER_ONLY)
    # convert to document base class, and save in db
    print(vehicle_clusters)


if __name__ == "__main__":
    main()
