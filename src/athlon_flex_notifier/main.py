"""Main entrypoint."""

from athlon_flex_api import AthlonFlexApi
from athlon_flex_api.models.vehicle_cluster import DetailLevel
from kink import inject

from athlon_flex_notifier.models.vehicle_availability import VehicleAvailability
from athlon_flex_notifier.models.vehicle_cluster import VehicleCluster
from athlon_flex_notifier.notifications.notifiers import Notifiers


@inject
def get_available_vehicle_clusters(api: AthlonFlexApi) -> list[VehicleCluster]:
    """Get all clusters with at least one unnotified availability."""
    return [
        VehicleCluster.from_base(base)
        for base in (
            api.vehicle_clusters(detail_level=DetailLevel.INCLUDE_VEHICLE_DETAILS)
        ).vehicle_clusters
    ]


def store_vehicle_availability(vehicle_clusters: list[VehicleCluster]) -> None:
    """Store all vehicle availabilities in the database."""
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
def main(notifiers: Notifiers) -> None:
    """Main entrypoint for testing."""  # noqa: D401
    clusters = get_available_vehicle_clusters()
    store_vehicle_availability(clusters)
    notifiers.notify()


if __name__ == "__main__":
    main()
