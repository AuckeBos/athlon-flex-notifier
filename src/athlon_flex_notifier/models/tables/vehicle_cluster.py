from athlon_flex_client.models.vehicle_cluster import (
    VehicleCluster as VehicleClusterBase,
)
from athlon_flex_client.models.vehicle_cluster import VehicleClusters
from kink import inject
from sqlmodel import Relationship

from athlon_flex_notifier.models.tables.base_table import BaseTable
from athlon_flex_notifier.models.tables.vehicle import Vehicle
from athlon_flex_notifier.upserter import Upserter
from athlon_flex_notifier.utils import time_it


class VehicleCluster(BaseTable, table=True):
    """Vehicle Cluster model.

    A Cluster defines a vehicle make and type. All registered
    cars belong to the cluster of its make and type.
    """

    __tablename__ = "vehicle_cluster"
    first_vehicle_id: str
    external_type_id: str
    make: str
    model: str
    latest_model_year: int
    vehicle_count: int
    min_price_in_euro_per_month: float
    fiscal_value_in_euro: float
    addition_percentage: float
    external_fuel_type_id: int
    max_co2_emission: int
    image_uri: str

    vehicles: list["Vehicle"] | None = Relationship(
        back_populates="vehicle_cluster",
        cascade_delete=True,
        sa_relationship_kwargs={"lazy": "joined"},
    )

    @staticmethod
    def business_keys() -> list[str]:
        return ["make", "model"]

    @staticmethod
    def scd1_attribute_keys() -> list[str]:
        """Any attributes that change based on any of the Vehicles available.

        Tracking history of these attributes would mean a new version whenever any
        of the vehicles in the cluster changes. This is not desired.
        """
        return [
            "first_vehicle_id",
            "latest_model_year",
            "vehicle_count",
            "min_price_in_euro_per_month",
            "fiscal_value_in_euro",
            "addition_percentage",
            "max_co2_emission",
            "image_uri",
        ]

    @classmethod
    def create_by_api_response(
        cls, vehicle_cluster_base: VehicleClusterBase
    ) -> "VehicleCluster":
        """Create a SQLModel instance from an API response."""
        data = {
            "first_vehicle_id": vehicle_cluster_base.firstVehicleId,
            "external_type_id": vehicle_cluster_base.externalTypeId,
            "make": vehicle_cluster_base.make,
            "model": vehicle_cluster_base.model,
            "latest_model_year": vehicle_cluster_base.latestModelYear,
            "vehicle_count": vehicle_cluster_base.vehicleCount,
            "min_price_in_euro_per_month": vehicle_cluster_base.minPriceInEuroPerMonth,
            "fiscal_value_in_euro": vehicle_cluster_base.fiscalValueInEuro,
            "addition_percentage": vehicle_cluster_base.additionPercentage,
            "external_fuel_type_id": vehicle_cluster_base.externalFuelTypeId,
            "max_co2_emission": vehicle_cluster_base.maxCO2Emission,
            "image_uri": vehicle_cluster_base.imageUri,
        }
        vehicle_cluster = VehicleCluster(**data)
        if vehicle_cluster_base.vehicles:
            vehicle_cluster.vehicles = [
                Vehicle.create_by_api_response(vehicle_base)
                for vehicle_base in vehicle_cluster_base.vehicles
            ]
        return vehicle_cluster

    @classmethod
    @inject
    def store_api_response(
        cls, vehicle_cluster_bases: VehicleClusters, upserter: Upserter
    ) -> list["VehicleCluster"]:
        """Create VehicleCluster instances from an API response, and upsert them.

        - Create the VehicleCluster instances, and upsert them
        - Update the Vehicles of each cluster, setting the correct cluster_id
            The cluster id was generated in _from_base, but if the cluster
            is not updated wrt the database, it should be the existing ID.
        - Upsert the vehicles
        - Update the options with the correct vehicle_id, same as with vehicles
        - Upsert the options
        - Return all active clusters

        """
        vehicle_clusters = {
            cluster.compute_key_hash(): cluster
            for cluster in [
                cls.create_by_api_response(vehicle_cluster)
                for vehicle_cluster in vehicle_cluster_bases.vehicle_clusters
            ]
        }
        with time_it("Upserting clusters"):
            vehicle_clusters_upserted = upserter.upsert(list(vehicle_clusters.values()))
        # set the correct vehicle_cluster_id on the vehicles
        vehicles = {}
        for cluster_key_hash, cluster in vehicle_clusters.items():
            for vehicle in cluster.vehicles:
                vehicle.vehicle_cluster_id = vehicle_clusters_upserted[
                    cluster_key_hash
                ].id
                vehicles[vehicle.compute_key_hash()] = vehicle
        with time_it("Upserting vehicles"):
            vehicles_upserted = upserter.upsert(list(vehicles.values()))
        # set the correct vehicle_id on the options
        options = []
        for vehicle_key_hash, vehicle in vehicles.items():
            for option in vehicle.options:
                option.vehicle_id = vehicles_upserted[vehicle_key_hash].id
                options.append(option)
        with time_it("Upserting options"):
            upserter.upsert(list(options))
        return VehicleCluster.all()

    @property
    def uri(self) -> str:
        return f"https://flex.athlon.com/app/showroom/{self.make}/{self.model}"

    def sized_image_uri(self, width: int) -> str:
        """Return the uri for an image of a given width."""
        return self.image_uri.replace("[#width#]", str(width))

    def __str__(self) -> str:
        return f"{self.make} {self.model}"
