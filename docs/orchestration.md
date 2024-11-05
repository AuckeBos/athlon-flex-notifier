# Introduction
Prefect is used for orchestration. Any code that should run periodically, should be deployed as a Prefect flow. Moreover, any ad-hoc flows which should be easily manually triggered, should also be deployed as a Prefect flow. The prefect frontend is used as entrypoint to the production server. 

# Deployments
All flows are defined in [flows.py](/src/athlon_flex_notifier/flows.py). All deployments use this file as entrypoint. 
We use the simplest way to deploy the flows: [the prefect serve method](https://docs-3.prefect.io/3.0/deploy/run-flows-in-local-processes). `flows.py` exposes a `work` method, in [worker.py](/src/athlon_flex_notifier/worker.py). This file is the entrypoint of the [Dockerfile](/infrastructure/Dockerfile), it serves all flows and includes the required schedules. 

The following flows exist:
- `refresh` Refreshes the database. It loads all data using the Api Client, and updates the database accordingly. It is ran every 10 minutes. 
- `notify` sends notifications to the user. It has two triggers:
  - Daily at `06:00`, using a `CronSchedule`.
  - Optionally, it is triggerd by events of type `prefect.flow-run.Completed`, emitted by flow runs of flows named `refresh`. If enabled, this ensures that we run the `notify` flow directly after each successfull `refresh`. This will update the user directly. If turned of, the user is updated daily, through the `CronSchedule. 
  
# Logging
Prefect is used to store the logs. If anything fails or doesn't work as expected, use Prefect as the first source of information. 