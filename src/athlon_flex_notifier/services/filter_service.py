import re
from logging import Logger
from typing import Any

from kink import inject

from athlon_flex_notifier.models.tables.base_table import BaseTable
from athlon_flex_notifier.models.views.vehicle_availability import VehicleAvailability


@inject
class FilterService:
    """Filter service. Can filter vehicle availabilities based on a filter dict."""

    logger: Logger

    @inject
    def __init__(self, logger: Logger) -> None:
        self.logger = logger

    def filter_vehicle_availabilities(
        self,
        vehicle_availabilities: list[VehicleAvailability],
        filters: dict[str, Any] | None = None,
    ) -> list[VehicleAvailability]:
        filters = filters or {}
        return [
            availability
            for availability in vehicle_availabilities
            if self.table_matches_filter(availability.vehicle, filters)
        ]

    def table_matches_filter(self, table: BaseTable, filters: dict[str, Any]) -> bool:
        for key, value in filters.items():
            if not hasattr(table, key):
                self.logger.warning("Model %s does not have attribute %s", table, key)
                return False
            if not re.match(value, getattr(table, key)):
                self.logger.debug(
                    "Model %s (%s) does not match filter %s=%s",
                    table,
                    table.compute_key_hash(),
                    key,
                    value,
                )
                return False
        return True
