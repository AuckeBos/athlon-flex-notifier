# Introduction
All parts of the project run in Docker containers. This page lists the containers, and their purpose.

## Containers
The following containers are defined in the main compose files ([docker-compose.yml](/infrastructure/docker-compose.yml), [development.yml](/infrastructure/development.yml), [portainer.yml](/infrastructure/portainer.yaml)). `development.yml` should be used during development, see [development.md](./development.md). `portainer.yml` should be used in production, see [README.md](../README.md). `docker-compose.yml` is a reference compose. 

### postgres
Contains the PostreSQL database. By default all data is stored in the `public` schema of the `athlon` database. A combination of [SQLModel](https://sqlmodel.tiangolo.com/) and [SqlAlchemy](https://www.sqlalchemy.org/) is used as ORM. We therefor do not write SQL queries manually in the repo, but use these ORMs to map objects to database tables. This libraries also automatically create our tables in the database. It is \#todo to use [alembic](https://alembic.sqlalchemy.org/) for migrations. It is also \#todo to remove the dependency of SQLModel, and solely depend on SQLAlchemy. Since SQLAlchemy V2, SQLModel doesn't have a large advantage over 'pure' SQLAlchemy, and is limited in its possibilities. And yes, it is also \#todo to track \#todos in Github' Issues. 

### pgadmin
Provides a browser interface to connect with Postgres databases. If preferred over local tools like SSMS, this web UI can be used to interact with the database.

### prefect-server
Runs the prefect server. Used to orchestrate all flows. It currently hosts a single flow: `refresh_and_notify`. This flow loads all available Vehicle clusters, Vehicles, and Vehicle options from the API. It then stores them full-load in the `athlon` database, using SCD2 to maintain history. After storing the data, it compares the [vw_vehicle_availability](/sql_scripts/vw_vehicle_availability.sql) view with the `notifications` table. If any availability is not yet notified, a notification email is sent with all new vehicles. Note that the CREATE VIEW script must be ran manually once, for this to work. See [datamodel.md](/docs/datamodel.md) for more information on the datamodel. 

### prefect-agent
This container runs one Prefect Agent, responsible for running the deployments configured on the server. When using [development.yml](/infrastructure/development.yml), this container uses the custom [Dockerfile](/infrastructure/Dockerfile). This file ensures all dependencies, including this repo, are installed properly. When running through [docker-compose.yml](/infrastructure/docker-compose.yml) or [portainer.yml](/infrastructure/portainer.yml), the container uses the pre-built image of that same dockerfile, as hosted on [Docker hub](https://hub.docker.com/repository/docker/auckebos/athlon-flex-notifier/general).

### watchtower
Watchtower for automatic pull deployment. This container runs on the production server (in my personal case a Raspberry Pi 4), and polls for updates on the image [auckebos/athlon-flex-notifier](https://hub.docker.com/repository/docker/auckebos/athlon-flex-notifier/general). If an update is found, it automatically pulls it, and restarts the [prefect-agent](#prefect-agent). When a PR is merged, the [deploy.yml](/.github/workflows/deploy.yml) builds a new image, and pushes it with the `latest` tag. This fully automates deployment. 