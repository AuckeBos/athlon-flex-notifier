from typing import TYPE_CHECKING, Optional

from athlon_flex_api.models.vehicle import Vehicle as VehicleBase
from kink import inject
from sqlalchemy import Engine, ForeignKeyConstraint
from sqlmodel import Field, Relationship, Session

from athlon_flex_notifier.models.base_model import BaseModel
from athlon_flex_notifier.models.option import Option

if TYPE_CHECKING:
    from athlon_flex_notifier.models.vehicle_availability import VehicleAvailability
    from athlon_flex_notifier.models.vehicle_cluster import VehicleCluster


class Vehicle(BaseModel, table=True):
    """Vehicle Cluster model.

    A Cluster defines a vehicle make and type. All registered
    cars belong to the cluster of its make and type.
    """

    model_config = {"protected_namespaces": ()}

    id: str = Field(primary_key=True)
    make: str
    model: str
    type: str
    model_year: int
    paint_id: str | None = None
    external_paint_id: str | None = None
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
    registered_mileage: float | None = None
    transmission_type: str | None = None
    avg_fuel_consumption: float | None = None
    type_spare_wheel: str | None = None
    fiscal_value_in_euro: float | None = None
    base_price_in_euro_per_month: float | None = None
    calculated_price_in_euro_per_month: float | None = None
    price_per_km: float | None = None
    fuel_price_per_km: float | None = None
    contribution_in_euro: float | None = None
    expected_fuel_cost_in_euro_per_month: float | None = None
    net_cost_in_euro_per_month: float | None = None
    vehicle_cluster: "VehicleCluster" = Relationship(
        back_populates="vehicles",
        sa_relationship_kwargs={
            "lazy": "joined",
        },
    )
    options: list[Option] = Relationship(back_populates="vehicle")
    vehicle_availabilities: list["VehicleAvailability"] = Relationship(
        back_populates="vehicle",
        sa_relationship_kwargs={
            "lazy": "joined",
        },
    )

    __table_args__ = (
        ForeignKeyConstraint(
            ["make", "model"], ["vehicle_cluster.make", "vehicle_cluster.model"]
        ),
    )

    @classmethod
    @inject
    def from_base(
        cls,
        vehicle_base: VehicleBase,
        vehicle_cluster: "VehicleCluster",
        database: Engine,
    ) -> "Vehicle":
        data = {
            "id": vehicle_base.id,
            "make": vehicle_base.make,
            "model": vehicle_base.model,
            "type": vehicle_base.type,
            "model_year": vehicle_base.modelYear,
            "paint_id": vehicle_base.paintId,
            "external_paint_id": vehicle_base.externalPaintId,
            "addition_percentage": vehicle_base.additionPercentage,
            "range_in_km": vehicle_base.rangeInKm,
            "external_fuel_type_id": vehicle_base.externalFuelTypeId,
            "external_type_id": vehicle_base.externalTypeId,
            "image_uri": vehicle_base.imageUri,
            "is_electric": vehicle_base.isElectric,
            "vehicle_cluster": vehicle_cluster,
        }
        if vehicle_base.details is not None:
            data = data | {
                "license_plate": vehicle_base.details.licensePlate,
                "color": vehicle_base.details.color,
                "official_color": vehicle_base.details.officialColor,
                "body_type": vehicle_base.details.bodyType,
                "emission": vehicle_base.details.emission,
                "registration_date": vehicle_base.details.registrationDate,
                "registered_mileage": vehicle_base.details.registeredMileage,
                "transmission_type": vehicle_base.details.transmissionType,
                "avg_fuel_consumption": vehicle_base.details.avgFuelConsumption,
                "type_spare_wheel": vehicle_base.details.typeSpareWheel,
            }
        if vehicle_base.pricing is not None:
            data = data | {
                "fiscal_value_in_euro": vehicle_base.pricing.fiscalValueInEuro,
                "base_price_in_euro_per_month": vehicle_base.pricing.basePricePerMonthInEuro,
                "calculated_price_in_euro_per_month": vehicle_base.pricing.calculatedPricePerMonthInEuro,
                "price_per_km": vehicle_base.pricing.pricePerKm,
                "fuel_price_per_km": vehicle_base.pricing.fuelPricePerKm,
                "contribution_in_euro": vehicle_base.pricing.contributionInEuro,
                "expected_fuel_cost_in_euro_per_month": vehicle_base.pricing.expectedFuelCostPerMonthInEuro,
                "net_cost_in_euro_per_month": vehicle_base.pricing.netCostPerMonthInEuro,
            }
        vehicle = Vehicle(**data).upsert()
        if vehicle_base.options:
            for option_base in vehicle_base.options:
                Option.from_base(option_base, vehicle)
        with Session(database) as session:
            return session.get(Vehicle, vehicle.id)

    @property
    def active_availability(self) -> Optional["VehicleAvailability"]:
        availabilities = [
            availability
            for availability in self.vehicle_availabilities
            if availability.is_currently_available
        ]
        if len(availabilities) > 1:
            raise ValueError(
                "There is more than one active availability for this vehicle"
            )
        return availabilities[0] if availabilities else None

    @property
    def has_active_availability(self) -> bool:
        return self.active_availability is not None

    def __str__(self) -> str:
        return f"{self.make} {self.model} {self.color} ({self.model_year})"
