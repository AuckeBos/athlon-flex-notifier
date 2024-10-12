from athlon_flex_api import AthlonFlexApi
from athlon_flex_api.models.vehicle_cluster import DetailLevel
from kink import inject
from sqlalchemy import Engine

from athlon_flex_notifier.models.vehicle_availability import VehicleAvailability
from athlon_flex_notifier.models.vehicle_cluster import VehicleCluster
from athlon_flex_notifier.notifications.notifier import Notifier


@inject
def load_data(api: AthlonFlexApi) -> list[VehicleCluster]:
    return [
        VehicleCluster.from_base(base)
        for base in (
            api.vehicle_clusters(detail_level=DetailLevel.INCLUDE_VEHICLE_DETAILS)
        ).vehicle_clusters
    ]


@inject
def create_vehicle_availability(
    vehicle_clusters: list[VehicleCluster], database: Engine
) -> None:
    existing_availabilities = {
        availability.id: availability for availability in VehicleAvailability.all()
    }
    for vehicle_cluster in vehicle_clusters:
        for vehicle in vehicle_cluster.vehicles:
            if availability := vehicle.active_availability:
                del existing_availabilities[availability.id]
                continue
            availability = VehicleAvailability.from_vehicle(vehicle)
    for availability in existing_availabilities.values():
        availability.deactivate()


@inject
def main(notifier: Notifier):
    # clusters = load_data()
    clusters = VehicleCluster.all()
    create_vehicle_availability(clusters)
    notifier.notify()


if __name__ == "__main__":
    main()
