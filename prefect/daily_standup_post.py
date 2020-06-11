import prefect
from prefect import Flow, Parameter, task
from prefect.client import Secret
from prefect.environments.execution.remote import RemoteEnvironment
from prefect.environments.storage import Docker
from prefect.schedules import CronSchedule

import datetime
import google.cloud.firestore
import json
import pendulum
import random
import requests
from google.oauth2 import service_account


SUPPORT_ROTATIONS = {
    "Monday": "<@UUSSRB4G7>",
    "Tuesday": "<@U0116UYJFGT> and <@UH8RAUN1Y>",
    "Wednesday": "<@UM8K2HFQC>",
    "Thursday": "<@UDKF9U8UC> and <@UTTUXQVN0>",
    "Friday": "<@ULWS8CZ47> and <@UBE4N2LG1>",
}


@task
def get_collection_name():
    date_format = "%Y-%m-%d"
    now = prefect.context["scheduled_start_time"]
    if isinstance(now, str):
        now = pendulum.parse(now)
    day_name = now.strftime("%A")
    weekend_offsets = {"Friday": 3, "Saturday": 2, "Sunday": 1}
    day_offset = weekend_offsets.get(day_name, 1)

    if day_name not in ["Saturday", "Sunday"]:
        if (now.hour < 14) or (now.hour == 14 and now.minute <= 2):
            return now.strftime(date_format)
        else:
            return (now + datetime.timedelta(days=day_offset)).strftime(date_format)
    else:
        return (now + datetime.timedelta(days=day_offset)).strftime(date_format)


@task
def get_latest_updates(date):
    """
    Returns dictionary of users -> updates
    """
    client = google.cloud.firestore.Client(project="prefect-marvin")
    collection = client.collection(f"standup/{date}/users")
    updates = collection.get()
    user_dict = {doc.id: (doc.to_dict() or {}).get("updates") for doc in updates}
    return user_dict


@task
def post_standup(updates, channel):
    if updates:
        public_msg = (
            f"<!here> are today's standup updates, brought to you by Prefect `v{prefect.__version__}`:\n"
            + "=" * 30
        )
        items = list(updates.items())
        random.shuffle(items)
        for user, update in items:
            public_msg += f"\n- *{user}*: {update}"
    else:
        public_msg = (
            f"<!here> No one told me anything, so I have no updates to share.\n"
        )

    on_call = SUPPORT_ROTATIONS[pendulum.now("utc").strftime("%A")]
    public_msg += f"\n\n{on_call} will be covering Slack support for the day."

    TOKEN = Secret("MARVIN_TOKEN")

    params = {
        "token": TOKEN.get(),
        "as_user": "true",
        "link_names": "true",
        "mrkdwn": "true",
        "channel": channel,
        "text": public_msg,
    }
    r = requests.post("https://slack.com/api/chat.postMessage", data=params)
    r.raise_for_status()
    if r.json()["ok"] is False:
        raise ValueError(r.json().get("error", "Requests error"))
    return r


weekday_schedule = CronSchedule(
    "30 9 * * 1-5", start_date=pendulum.parse("2017-03-24", tz="US/Eastern")
)
environment = RemoteEnvironment(executor="prefect.engine.executors.SynchronousExecutor")
storage = Docker(
    prefect_version="master",
    base_image="python:3.6",
    registry_url="gcr.io/tenant-staging-d49111/flows/",
    python_dependencies=[
        "google-cloud-firestore",
        "requests",
        "dask_kubernetes",
        "kubernetes",
    ],
    files={
        "/Users/chris/Developer/marvin/prefect-marvin-e5f415f8d2b2.json": "/root/.prefect/prefect-marvin-credentials.json"
    },
    env_vars={
        "GOOGLE_APPLICATION_CREDENTIALS": "/root/.prefect/prefect-marvin-credentials.json"
    },
)


with Flow(
    "Daily Standup",
    schedule=weekday_schedule,
    environment=environment,
    storage=storage,
) as flow:
    standup_channel = Parameter("standup_channel", default="CBH18KG8G")
    res = post_standup(get_latest_updates(get_collection_name()), standup_channel)
