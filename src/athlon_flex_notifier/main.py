from athlon_flex_api import AthlonFlexApi
from kink import inject

# Force bootstrap
from athlon_flex_notifier import *


@inject
def main(api: AthlonFlexApi):
    vehicle_clusters = api.vehicle_clusters()
    # convert to document base class, and save in db
    print(vehicle_clusters)


if __name__ == "__main__":
    main()
