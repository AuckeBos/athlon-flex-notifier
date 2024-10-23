from uuid import UUID

from athlon_flex_api.models.vehicle import Vehicle as VehicleBase
from sqlmodel import Field, Relationship

from athlon_flex_notifier.models.base_model import BaseModel
from athlon_flex_notifier.models.vehicle import Vehicle


class Option(BaseModel, table=True):
    """Vehicle option.

    Example: Trekhaak.
    """

    athlon_id: str
    externalId: str
    optionName: str
    included: bool
    vehicle_id: UUID | None = Field(foreign_key="vehicle.id", nullable=False)
    vehicle: Vehicle = Relationship(back_populates="options")

    @staticmethod
    def business_keys() -> list[str]:
        return ["athlon_id", "vehicle_id"]

    @staticmethod
    def from_base(option_base: VehicleBase.Option) -> "Option":
        """Create a SQLModel instance from an API vehicle, and upsert it.

        Note that the vehicle_id is not set here. Since it is required in the
        DB, this property must be set before the vehicle can be upserted.
        """
        data = {
            "athlon_id": option_base.id,
            "externalId": option_base.externalId,
            "optionName": option_base.optionName,
            "included": option_base.included,
        }
        return Option(**data)
