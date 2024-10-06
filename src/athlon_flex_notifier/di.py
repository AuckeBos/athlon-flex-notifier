import os

from athlon_flex_api.api import AthlonFlexApi
from dependency_injector import containers, providers


class Container(containers.DeclarativeContainer):
    athlon_api = providers.Singleton(
        AthlonFlexApi,
        email=os.environ["ATHLON_USERNAME"],
        password=os.environ["ATHLON_PASSWORD"],
    )
