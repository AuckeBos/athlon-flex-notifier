from typing import TYPE_CHECKING

from athlon_flex_api.models.vehicle_cluster import VehicleCluster as VehicleClusterBase
from sqlmodel import Field, Relationship

from athlon_flex_notifier.models.base_model import BaseModel
from athlon_flex_notifier.models.vehicle import Vehicle

if TYPE_CHECKING:
    from athlon_flex_notifier.models.vehicle_availability import VehicleAvailability


class VehicleCluster(BaseModel, table=True):
    """Vehicle Cluster model.

    A Cluster defines a vehicle make and type. All registered
    cars belong to the cluster of its make and type.
    """

    __tablename__ = "vehicle_cluster"
    first_vehicle_id: str
    external_type_id: str
    make: str = Field(primary_key=True)
    model: str = Field(primary_key=True)
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
    vehicle_availabilities: list["VehicleAvailability"] | None = Relationship(
        back_populates="vehicle_cluster",
        cascade_delete=True,
        sa_relationship_kwargs={"lazy": "joined"},
    )

    @classmethod
    def _from_base(cls, vehicle_cluster_base: VehicleClusterBase) -> "VehicleCluster":
        """Create a SQLModel instance from an API option."""
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
                Vehicle.from_base(vehicle_base)
                for vehicle_base in vehicle_cluster_base.vehicles
            ]
        return vehicle_cluster

    @classmethod
    def from_base(cls, *vehicle_clusters: VehicleClusterBase) -> list["VehicleCluster"]:
        """Create instances and upsert them."""
        return cls.upsert(*[cls._from_base(base) for base in vehicle_clusters])

    @property
    def is_available(self) -> bool:
        return len(self.vehicle_availabilities) > 0

    @property
    def unnotified_availabilities(self) -> list["VehicleAvailability"]:
        """All active availabilities that are not notified yet."""
        return [
            availability
            for availability in self.vehicle_availabilities
            if not availability.notified and availability.is_currently_available
        ]

    @property
    def should_notify(self) -> bool:
        """Notify about a cluster if at least one availability is not notified."""
        return len(self.unnotified_availabilities) > 0

    @property
    def uri(self) -> str:
        return f"https://flex.athlon.com/app/showroom/{self.make}/{self.model}"

    def sized_image_uri(self, width: int) -> str:
        """Return the uri for an image of a given width."""
        return self.image_uri.replace("[#width#]", str(width))

    def __str__(self) -> str:
        return f"{self.make} {self.model}"
