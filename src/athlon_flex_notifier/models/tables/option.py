from uuid import UUID

from athlon_flex_client.models.vehicle import Vehicle as VehicleBase
from sqlmodel import Field, Relationship

from athlon_flex_notifier.models.tables.base_table import BaseTable
from athlon_flex_notifier.models.tables.vehicle import Vehicle


class Option(BaseTable, table=True):
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
    def scd1_attribute_keys() -> list[str]:
        return ["vehicle_id"]

    @staticmethod
    def create_by_api_response(option_base: VehicleBase.Option) -> "Option":
        """Create a SQLModel instance from an API reponse.

        Note that the vehicle_id is not set here. Since it is required in the
        DB, this property must be set before the option can be upserted.
        """
        data = {
            "athlon_id": option_base.id,
            "externalId": option_base.externalId,
            "optionName": option_base.optionName,
            "included": option_base.included,
        }
        return Option(**data)
