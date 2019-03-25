import prefect
from prefect import Flow, task
from prefect.client import Secret
from prefect.engine.result_handlers import JSONResultHandler
from prefect.environments.kubernetes import DaskOnKubernetesEnvironment
from prefect.schedules import IntervalSchedule
from prefect.tasks.airtable import WriteAirtableRow

import datetime
import json
import pendulum
import requests


@task
def get_latest_repo_stats():
    MARVIN_ACCESS_TOKEN = Secret("MARVIN_ACCESS_TOKEN").get()
    url = "https://api.github.com/repos/PrefectHQ/prefect"
    headers = {"AUTHORIZATION": f"token {MARVIN_ACCESS_TOKEN}"}
    resp = requests.get(url, headers=headers)
    resp.raise_for_status()
    data = resp.json()
    return {
        "Timestamp": pendulum.now("utc").isoformat(),
        "Stars": data["stargazers_count"],
        "Watchers": data["subscribers_count"],
    }


airtable = WriteAirtableRow(base_key="app7erPQcwXMyhbb4", table_name="Stars")
hourly_schedule = IntervalSchedule(
    start_date=pendulum.parse("2019-03-23"), interval=datetime.timedelta(hours=4)
)
env = DaskOnKubernetesEnvironment(
    base_image="python:3.6",
    registry_url="gcr.io/prefect-dev/flows/",
    python_dependencies=["airtable-python-wrapper", "kubernetes", "dask-kubernetes"],
)


with Flow("github-stars", schedule=hourly_schedule, environment=env) as flow:
    result = airtable(get_latest_repo_stats)
