import docker
import prefect
from prefect import Flow, Parameter, task
from prefect.client import Secret
from prefect.executors import LocalExecutor
from prefect.environments.storage import Docker
from prefect.schedules import CronSchedule

import datetime
import google.cloud.firestore
import pendulum
import random
import requests
from google.oauth2 import service_account


SUPPORT_ROTATIONS = {
    "Monday": "<@UDKF9U8UC> and <@UUSSRB4G7>",  # Dylan and  Kyle MW
    "Tuesday": "<@ULWS8CZ47> and <@U01CB54HF8R>",  # Mariia and Jenny
    "Wednesday": "<@U0116UYJFGT>",  # Jim
    "Thursday": "<@U01D3K2GALQ>",  # Michael
    "Friday": "<@UM8K2HFQC>",  # nicholas
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
        if (now.hour < 14) or (now.hour == 14 and now.minute <= 33):
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
            f"<!here>'s the midweek update, brought to you by Prefect `v{prefect.__version__}`:\n"
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


# Post the midweek update on Wednesday morning
weekday_schedule = CronSchedule(
    "30 9 * * 3", start_date=pendulum.parse("2017-03-24", tz="US/Eastern")
)


with Flow("Daily Standup", schedule=weekday_schedule, executor=LocalExecutor()) as flow:
    standup_channel = Parameter("standup_channel", default="CBH18KG8G")
    res = post_standup(get_latest_updates(get_collection_name()), standup_channel)


if __name__ == "__main__":
    default_client = docker.from_env()
    storage = Docker(
        base_url=default_client.api.base_url,
        tls_config=docker.TLSConfig(default_client.api.cert),
        registry_url="gcr.io/prefect-tenant-0c5400/flows/",
        image_name="standup-flow",
        image_tag="latest",
        python_dependencies=[
            "google-cloud-firestore",
            "requests",
            "dask_kubernetes",
            "kubernetes",
        ],
        files={
            "/firebase-credentials.json": "/root/.prefect/prefect-marvin-credentials.json"
        },
        env_vars={
            "GOOGLE_APPLICATION_CREDENTIALS": "/root/.prefect/prefect-marvin-credentials.json"
        },
    )
    flow.storage = storage
    flow.register("Marvin", idempotency_key=flow.serialized_hash())
