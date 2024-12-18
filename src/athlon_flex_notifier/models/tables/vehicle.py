from typing import TYPE_CHECKING, Any, ClassVar
from uuid import UUID

from athlon_flex_client.models.vehicle import Vehicle as VehicleBase
from sqlmodel import Field, Relationship

from athlon_flex_notifier.models.tables.base_table import BaseTable

if TYPE_CHECKING:
    from athlon_flex_notifier.models.tables.option import Option
    from athlon_flex_notifier.models.tables.vehicle_cluster import VehicleCluster


class Vehicle(BaseTable, table=True):
    """Vehicle model.

    A Vehicle defines a specific vehicle configuration.
    For example one instance of the Opel Corsa E. It belongs to the VehicleCluster
    of its make and type.

    The following fields differ based on whether the user is logged in:
        - calculatedPricePerMonthInEuro is updated when the user is logged in
        - contributionInEuro is updated when the user is logged in
        - netCostPerMonthInEuro is not present when the user is not logged in

    """

    model_config: ClassVar[dict[str, Any]] = {"protected_namespaces": ()}
    athlon_id: str
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
    uri: str
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
    vehicle_cluster_id: UUID | None = Field(
        foreign_key="vehicle_cluster.id", nullable=False
    )
    vehicle_cluster: "VehicleCluster" = Relationship(
        back_populates="vehicles",
        sa_relationship_kwargs={
            "lazy": "joined",
        },
    )
    options: list["Option"] = Relationship(
        back_populates="vehicle",
        cascade_delete=True,
    )

    @staticmethod
    def business_keys() -> list[str]:
        return ["athlon_id"]

    @staticmethod
    def scd1_attribute_keys() -> list[str]:
        return ["vehicle_cluster_id"]

    @classmethod
    def create_by_api_response(cls, vehicle_base: VehicleBase) -> "Vehicle":
        """Create a SQLModel instance by an API response.

        Note that the vehicle_cluster_id is not set here. Since it is required in the
        DB, this property must be set before the vehicle can be upserted.
        """
        from athlon_flex_notifier.models.tables.option import Option

        data = {
            "athlon_id": vehicle_base.id,
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
            "uri": vehicle_base.uri,
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
                "base_price_in_euro_per_month": (
                    vehicle_base.pricing.basePricePerMonthInEuro
                ),
                "calculated_price_in_euro_per_month": (
                    vehicle_base.pricing.calculatedPricePerMonthInEuro
                ),
                "price_per_km": vehicle_base.pricing.pricePerKm,
                "fuel_price_per_km": vehicle_base.pricing.fuelPricePerKm,
                "contribution_in_euro": vehicle_base.pricing.contributionInEuro,
                "expected_fuel_cost_in_euro_per_month": (
                    vehicle_base.pricing.expectedFuelCostPerMonthInEuro
                ),
                "net_cost_in_euro_per_month": (
                    vehicle_base.pricing.netCostPerMonthInEuro
                ),
            }
        vehicle = Vehicle(**data)
        if vehicle_base.options:
            vehicle.options = [
                Option.create_by_api_response(option_base)
                for option_base in vehicle_base.options
            ]
        return vehicle

    @property
    def has_active_availability(self) -> bool:
        return self.active_availability is not None

    def sized_image_uri(self, width: int) -> str:
        """Return the uri for an image of a given width."""
        return self.image_uri.replace("[#width#]", str(width))

    def __str__(self) -> str:
        return f"{self.make} {self.model} {self.color} {self.model_year}"
