from typing import Any, Dict, List

from pydantic import BaseModel, ValidationError
from pydantic.schema import schema

from athlon_flex_notifier.models.tables.vehicle import Vehicle
from athlon_flex_notifier.models.tables.vehicle_cluster import VehicleCluster
from logging import Logger
from kink import inject


@inject
class FilterService:
    logger: Logger

    def __init__(self, logger: Logger) -> None:
        self.logger = logger

    def filter_vehicle_clusters(
        self, vehicle_clusters: List[VehicleCluster], filter_parameters: Dict[str, Any]
    ) -> List[VehicleCluster]:
        filtered_clusters = []
        for cluster in vehicle_clusters:
            if self._apply_filter(cluster, filter_parameters):
                filtered_clusters.append(cluster)
        self.logger.info(f"Filtered {len(vehicle_clusters) - len(filtered_clusters)} vehicle clusters out of {len(vehicle_clusters)}")
        return filtered_clusters

    def filter_vehicles(
        self, vehicles: List[Vehicle], filter_parameters: Dict[str, Any]
    ) -> List[Vehicle]:
        filtered_vehicles = []
        for vehicle in vehicles:
            if self._apply_filter(vehicle, filter_parameters):
                filtered_vehicles.append(vehicle)
        self.logger.info(f"Filtered {len(vehicles) - len(filtered_vehicles)} vehicles out of {len(vehicles)}")
        return filtered_vehicles

    def _apply_filter(self, obj: Any, filter_parameters: Dict[str, Any]) -> bool:
        for key, value in filter_parameters.items():
            if not hasattr(obj, key) or getattr(obj, key) != value:
                return False
        return True

    def validate_filter_parameters(self, filter_parameters: Dict[str, Any]) -> None:
        vehicle_schema = self._generate_schema(Vehicle)
        vehicle_cluster_schema = self._generate_schema(VehicleCluster)
        combined_schema = {
            "type": "object",
            "properties": {
                "vehicle": vehicle_schema,
                "vehicle_cluster": vehicle_cluster_schema,
            },
        }
        try:
            BaseModel.parse_obj(filter_parameters, combined_schema)
        except ValidationError as e:
            self.logger.error(f"Invalid filter parameters: {e}")
            raise e

    def _generate_schema(self, model: BaseModel) -> Dict[str, Any]:
        return schema([model], ref_prefix="#/components/schemas/")["definitions"][
            model.__name__
        ]
