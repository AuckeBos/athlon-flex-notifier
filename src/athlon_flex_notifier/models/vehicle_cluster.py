from athlon_flex_api.models.vehicle_cluster import VehicleCluster as VehicleClusterBase
from kink import inject
from sqlalchemy import Engine
from sqlmodel import Field, Relationship, Session

from athlon_flex_notifier.models.base_model import BaseModel
from athlon_flex_notifier.models.vehicle import Vehicle


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

    @classmethod
    @inject
    def from_base(
        cls, vehicle_cluster_base: VehicleClusterBase, database: Engine
    ) -> "VehicleCluster":
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
        vehicle_cluster = VehicleCluster(**data).upsert()
        if vehicle_cluster_base.vehicles:
            for vehicle_base in vehicle_cluster_base.vehicles:
                Vehicle.from_base(vehicle_base, vehicle_cluster)
        with Session(database) as session:
            return session.get(
                VehicleCluster, (vehicle_cluster.make, vehicle_cluster.model)
            )