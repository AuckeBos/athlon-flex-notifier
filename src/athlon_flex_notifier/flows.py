from kink import di
from prefect import flow, serve
from prefect.client.schemas.schedules import CronSchedule
from prefect.events import DeploymentEventTrigger
from logging import Logger

from athlon_flex_notifier.notifications.notifiers import Notifiers
from athlon_flex_notifier.refresher import (
    Refresher,
)
from athlon_flex_notifier.services.filter_service import FilterService
from pydantic import ValidationError


@flow
def refresh() -> None:
    """Update the database with the current vehicles."""
    di[Refresher].refresh()


@flow
def notify(filter_parameters: dict | None = None) -> None:
    """Notify the user about new vehicles."""
    logger = di[Logger]
    if filter_parameters:
        logger.info(f"Filter parameters provided: {filter_parameters}")
        try:
            FilterService.validate_filter_parameters(filter_parameters)
        except ValidationError as e:
            logger.error(f"Invalid filter parameters: {e}")
            return
    di[Notifiers](filter_parameters=filter_parameters).notify()


def work() -> None:
    """Create the deployments."""
    serve(
        refresh.to_deployment(
            name="refresh",
            version="2024.11.11",
            schedules=[
                CronSchedule(
                    cron="*/10 * * * *",
                )
            ],
        ),
        notify.to_deployment(
            name="notify",
            version="2024.11.11",
            triggers=[
                DeploymentEventTrigger(
                    name="notify_on_refresh",
                    enabled=False,
                    match_related={"prefect.resource.name": "refresh"},
                    expect=["prefect.flow-run.Completed"],
                )
            ],
            schedules=[
                CronSchedule(
                    cron="0 6 * * *",
                    timezone="Europe/Amsterdam",
                )
            ],
        ),
    )
