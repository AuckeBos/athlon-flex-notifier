# Athlon Flex Notifier

## Table of contents
- [Athlon Flex Notifier](#athlon-flex-notifier)
  - [Table of contents](#table-of-contents)
  - [Introduction](#introduction)
  - [Athlon Flex API](#athlon-flex-api)
  - [Installation \& Configuration](#installation--configuration)
    - [Athlon](#athlon)
    - [Postgres](#postgres)
    - [PGAdmin](#pgadmin)
    - [Email](#email)
    - [Prefect](#prefect)
  - [Usage](#usage)
  - [Technical documentation](#technical-documentation)
  - [Licence](#licence)
  - [Contributing](#contributing)
  - [Contact](#contact)



## Introduction
This repository contains a tool to automatically receive notifications when new vehicles become available on the [Athlon Flex Showroom](https://flex.athlon.com/app/showroom). I created this for personal use. The available cars in the showroom rotate quickly. I noticed I was often either too late to order a new vehicle, or constantly checking the showroom for new availabilities. This repository automates this proces for me. It is structured in such a way that it is easly deployable for anyone who would like to do so; the docs will describe the steps that need to be taken for this. 

## Athlon Flex API
The showroom uses a REST api under the hood. I created a Python package to smoothen interaction with the API. The package is hosted on [Pypi](https://pypi.org/project/athlon-flex-client/); the docs are hosted on [Readthedocs](https://athlon-flex-api.readthedocs.io/en/latest/). The client exposes functions to load Vehicle Clusters and Vehicles. While this client is at the core of this project, this repository is focussed on storing and versioning the data it returns. Goals for storing this data are:
- Sending notifications when a Vehicle becomes available that wasn't available before.
- Providing the possibility to query (the history of) all vehicles, using PostreSQL.
- Providing the possibility to create a dashboard on this, just for fun!


## Installation & Configuration
The easiest way to get up and running, is using Docker compose. Moreover, to easily manage and monitor all container, you can use Portainer. To install Docker and Docker compose, follow the instructions on the [Docker website](https://docs.docker.com/get-docker/). To install Portainer, follow the instructions on the [Portainer website](https://www.portainer.io/installation/).

With portainer up and running, create a new stack, using [portainer.yaml](infrastructure/portainer.yml). Use [.docker-env.example](.docker-env.example) with values of your choice, and add them to the stack. The following environment variables are used:

### Athlon
- `ATHLON_USERNAME` and `ATHLON_PASSWORD` allow the Athlon Flex Client to load information using your personal profile. The main benefit is that the API responses will include computed Net Costs based on your profile (Lease Budget). Note that the project will always store all vehicles, even those not leasable by your profile. These environment variables are optional; without them the API is called anonymously.
- `GROSS_YEARLY_INCOME` and `APPLY_LOONHEFFINGSKORTING` can be used to provide the API Client with extra information, to be able to properly compute the Net Monthly Cost of a vehicle. When first logging in to the Flex Showroom, a popup is shown which asks for this same information. The information is then stored in a cookie, and used when browsing the showroom. These environment veriables mimic this behaviour. They are optional.

### Postgres
A Postgres database is used to store all data. The following environment variables are required: `POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_HOST`, `POSTGRES_PORT`, `POSTGRES_DB`. When running with `portainer`, you probably only need to change the username and password.

### PGAdmin
The stack also includes a PGAdmin UI. Environment variables `PGADMIN_DEFAULT_EMAIL` and `PGADMIN_DEFAULT_PASSWORD` indicate the default Admin login for this server. They do not need to be equal to the PogreSQL env vars. They are not related to the PostgresDB whatsoever. After first login, you'll also still need to add the PostgresDB as a server. Note that you need to use the internal docker endpoint and url, which are `postgres` and `5432` respectively. 

### Email
The project currently only supports sending email using Gmail. Environment variables `EMAIL_FROM` and `GOOGLE_APP_PASSWORD` are required to get this to work. Take a look at the [Google docs](https://developers.google.com/workspace/guides/create-credentials) to create a Google password for your personal account. _Using your regular password will not work_. `EMAIL_TO` indicates the recipient email (multiple recipients is not yet supported).

### Prefect
Prefect is used as orchestration engine. `PREFECT_API_URL` indicates the internal app url. You most likely do not need to change this value. 



## Usage
Given that you have created env file `.docker-env` in the root of the repo, spin up all infrastructure using
```sh
docker-compose -f infrastructure/development.yml --env-file ./.docker-env -p athlon up
```
After all images are downloaded and the containers are built, all infra is running. Prefect will now load and store all Athlon data every 10 minutes. History will be maintained for all entities, using SCD2 logic. The following URLs are relevent:
- [http://localhost:13001](http://localhost:13001) is the url for the PostgresDB. You can use it to connect with the database, for example using [Azure Data Studio](https://azure.microsoft.com/en-us/products/data-studio/) with the [PostgreSQL extension](https://learn.microsoft.com/en-us/azure-data-studio/extensions/postgres-extension).
- [http://localhost:13002](http://localhost:13002) is the url for PGAdmin. You can login using the values of env vars `PGADMIN_DEFAULT_EMAIL` and `PGADMIN_DEFAULT_PASSWORD`. You can add the PostgresDB by using hostname `postgres` and port `5432`. 
- [http://localhost:13003](http://localhost:13003) Is the url for the Prefect server. You will find one flow with one deployment. The deployment will run every 10 minutes, and store the data and send a notification email if new vehicles are available. 

For the notification mechanism to work, view `public.vw_vehicle_availability` must exist. You should manually run [vw_vehicle_availability.sql](/sql_scripts/vw_vehicle_availability.sql) once, on the PostgresDB. Automating this is \#todo. 

## Technical documentation
Please find technical documentation in the [docs](docs) folder. Moreover, some subfolders contain markdown files with details on the classes and functions in that folder.

## Licence
This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Contributing
Contributions are most welcome. I've not yet setup a contributing guide, but feel free to reach out to me if you'd like to contribute to and/or use this project.

## Contact
Feel free to contact me on [LinkedIn](https://www.linkedin.com/in/auckebos/). 