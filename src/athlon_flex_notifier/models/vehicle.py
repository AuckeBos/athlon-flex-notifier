from typing import TYPE_CHECKING

from sqlmodel import Field, Relationship, SQLModel

from athlon_flex_notifier.models.vehicle_option import VehicleOption

if TYPE_CHECKING:
    from athlon_flex_notifier.models.option import Option


class Vehicle(SQLModel, table=True):
    """Vehicle Cluster model.

    A Cluster defines a vehicle make and type. All registered
    cars belong to the cluster of its make and type.
    """

    id: str = Field(primary_key=True)
    make: str
    model: str
    type: str
    model_year: int
    paint_id: str | None = None
    external_paint_id: str | None = None
    fiscal_value_in_euro: float | None = None
    addition_percentage: float | None = None
    range_in_km: int
    external_fuel_type_id: int
    external_type_id: str
    image_uri: str | None = None
    is_electric: bool | None = None
    license_plate: str | None = None
    color: str | None = None
    official_color: str | None = None
    body_type: str | None = None
    emission: float | None = None
    registration_date: str | None = None
    registration_mileage: int | None = None
    transmission_type: str | None = None
    avg_fuel_consumption: float | None = None
    type_spare_wheel: str | None = None
    final_fiscal_value_in_euro: float | None = None
    base_price_in_euro_per_month: float | None = None
    calculated_price_in_euro_per_month: float | None = None
    price_per_km: float | None = None
    fuel_price_per_km: float | None = None
    contribution_in_euro: float | None = None
    expected_fuel_cost_in_euro_per_month: float | None = None
    net_cost_in_euro_per_month: float | None = None
    options: list["Option"] = Relationship(
        back_populates="vehicles", link_model=VehicleOption
    )
