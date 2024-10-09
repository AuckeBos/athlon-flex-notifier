from typing import TYPE_CHECKING

from sqlmodel import Field, Relationship, SQLModel

if TYPE_CHECKING:
    from athlon_flex_notifier.models.vehicle import Vehicle


class VehicleCluster(SQLModel, table=True):
    """Vehicle Cluster model.

    A Cluster defines a vehicle make and type. All registered
    cars belong to the cluster of its make and type.
    """

    id: int | None = Field(default=None, primary_key=True)
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
    )
