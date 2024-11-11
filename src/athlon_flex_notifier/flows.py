from kink import di
from prefect import flow, serve
from prefect.client.schemas.schedules import CronSchedule
from prefect.events import DeploymentEventTrigger

from athlon_flex_notifier.notifications.notifiers import Notifiers
from athlon_flex_notifier.refresher import (
    Refresher,
)


@flow
def refresh() -> None:
    """Update the database with the current vehicles."""
    di[Refresher].refresh()


@flow
def notify() -> None:
    """Notify the user about new vehicles."""
    di[Notifiers].notify()


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
                    enabled=True,
                    match_related={"prefect.resource.name": "refresh"},
                    expect=["prefect.flow-run.Completed"],
                )
            ],
            schedules=[
                CronSchedule(
                    cron="0 6 * * *",
                )
            ],
        ),
    )
