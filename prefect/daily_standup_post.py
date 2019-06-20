import prefect
from prefect import Flow, Parameter, task
from prefect.client import Secret
from prefect.engine.result_handlers import JSONResultHandler
from prefect.environments.storage import Docker
from prefect.schedules import CronSchedule

import datetime
import google.cloud.firestore
import json
import pendulum
import random
import requests
from google.oauth2 import service_account


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
    public_msg = (
        f"<!here> are today's standup updates, brought to you by Prefect `v{prefect.__version__}`:\n"
        + "=" * 30
    )
    items = list(updates.items())
    random.shuffle(items)
    for user, update in items:
        public_msg += f"\n- *{user}*: {update}"

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
    "0 9 * * 1-5", start_date=pendulum.parse("2017-03-24", tz="US/Eastern")
)
storage = Docker(
    prefect_version="master",
    base_image="python:3.6",
    registry_url="gcr.io/prefect-dev/flows/",
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


def notify_chris(flow, state):
    url = Secret("SLACK_WEBHOOK_URL").get()
    message = f"@chris, the daily standup flow failed; here is everything I know about the Flow state: ```{state.serialize()}```"
    r = requests.post(
        url, json={"text": message, "mrkdwn": "true", "link_names": "true"}
    )


with Flow(
    "post-standup",
    schedule=weekday_schedule,
    storage=storage,
    on_failure=notify_chris,
    result_handler=JSONResultHandler(),
) as flow:
    standup_channel = Parameter("standup_channel", default="CANLZB1L3")
    res = post_standup(get_latest_updates(get_collection_name()), standup_channel)