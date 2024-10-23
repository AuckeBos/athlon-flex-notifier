from athlon_flex_api.models.vehicle import Vehicle as VehicleBase
from sqlmodel import Field, Relationship

from athlon_flex_notifier.models.base_model import BaseModel
from athlon_flex_notifier.models.vehicle import Vehicle


class Option(BaseModel, table=True):
    """Vehicle option.

    Example: Trekhaak.
    """

    id: str
    externalId: str
    optionName: str
    included: bool
    vehicle_key_hash: str = Field(foreign_key="vehicle.key_hash")
    vehicle: Vehicle = Relationship(back_populates="options")

    @staticmethod
    def business_keys() -> list[str]:
        return ["id", "vehicle_key_hash"]

    @staticmethod
    def from_base(option_base: VehicleBase.Option, vehicle: Vehicle) -> "Option":
        """Create a SQLModel instance from an API option, and upsert it."""
        data = {
            "id": option_base.id,
            "externalId": option_base.externalId,
            "optionName": option_base.optionName,
            "included": option_base.included,
            "vehicle_key_hash": Vehicle.compute_key_hash(vehicle),
        }
        return Option(**data)
