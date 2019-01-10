from prefect import Flow, Parameter, task
from prefect.client import Secret
from prefect.environments import ContainerEnvironment
from prefect.schedules import CronSchedule

import datetime
import google.cloud.firestore
import json
import requests
from google.oauth2 import service_account


@task
def get_collection_name():
    date_format = "%Y-%m-%d"
    now = datetime.datetime.utcnow()
    day_name = now.strftime("%A")
    weekend_offsets = {"Friday": 3, "Saturday": 2, "Sunday": 1}
    day_offset = weekend_offsets.get(day_name, 1)

    if day_name not in ["Saturday", "Sunday"]:
        if (now.hour < 14) or (now.hour == 14 and now.minute <= 1):
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
    public_msg = "<!here> are today's standup updates:\n" + "=" * 30
    for user, update in updates.items():
        public_msg += f"\n*{user}*: {update}"

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


weekday_schedule = CronSchedule("0 14 * * 1-5")
env = ContainerEnvironment(
    base_image="python:3.6",
    registry_url="gcr.io/prefect-dev/flows/",
    python_dependencies=["google-cloud-firestore", "requests"],
    files={
        "/Users/chris/Developer/marvin/prefect-marvin-e5f415f8d2b2.json": "/root/.prefect/prefect-marvin-credentials.json"
    },
    env_vars={
        "GOOGLE_APPLICATION_CREDENTIALS": "/root/.prefect/prefect-marvin-credentials.json"
    },
)


with Flow("post-standup", schedule=weekday_schedule, environment=env) as flow:
    standup_channel = Parameter("standup_channel", default="CANLZB1L3")
    res = post_standup(get_latest_updates(get_collection_name()), standup_channel)
