from athlon_flex_api.api import AthlonFlexApi
from athlon_flex_api.models.vehicle_cluster import DetailLevel
from dependency_injector.wiring import Provide, inject

from athlon_flex_notifier.di import Container


@inject
def main(api: AthlonFlexApi = Provide[Container.athlon_api]):
    vehicle_clusters = api.vehicle_clusters(detail_level=DetailLevel.CLUSTER_ONLY)
    # convert to document base class, and save in db
    print(vehicle_clusters)


if __name__ == "__main__":
    # why do we need to rewire?
    container = Container()
    container.wire(modules=[__name__])
    main()
