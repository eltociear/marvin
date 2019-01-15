from prefect import Flow, Parameter, task
from prefect.client import Secret
from prefect.environments import ContainerEnvironment
from prefect.schedules import CronSchedule
from prefect.engine.signals import SKIP
from prefect.utilities.tasks import unmapped

import datetime
import google.cloud.firestore
import json
import requests
from google.oauth2 import service_account


@task
def get_standup_date():
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
def get_team():
    """
    Retrieve all current full-time Slack users.

    Returns:
        - a list of (user name, Slack User ID) tuples
    """
    TOKEN = Secret("MARVIN_TOKEN")
    params = {"token": TOKEN.get()}
    r = requests.post("https://slack.com/api/users.list", data=params)
    r.raise_for_status()
    if r.json()["ok"] is False:
        raise ValueError(r.json().get("error", "Requests error"))

    user_dict = {}
    user_data = json.loads(r.text)["members"]
    for user in user_data:
        if (
            not user["is_bot"]
            and user["name"] not in ("slackbot", "test-user")
            and not user["is_ultra_restricted"]
        ):
            user_dict[user["name"]] = user["id"]
    return [(name, id) for name, id in user_dict.items()]


@task
def is_reminder_needed(user_info, current_updates):
    user_name, user_id = user_info
    if current_updates.get(user_name) is not None:
        raise SKIP(f"{user_name} has already provided an update")
    else:
        return user_info


@task
def send_reminder(user_info):
    user_name, user_id = user_info
    TOKEN = Secret("MARVIN_TOKEN")

    ## get private channel ID for this user
    params = {"token": TOKEN.get(), "user": user_id}
    r = requests.post("https://slack.com/api/im.open", data=params)
    channel_id = json.loads(r.text)["channel"]["id"]

    params.pop("user")
    text = (
        f"Hi {user_name}! I haven't heard from you yet; what updates do you have for the team today? Please respond by using the slash command `/standup`,  and remember: your response will be shared!",
    )
    params.update(
        {
            "as_user": "true",
            "link_names": "true",
            "mrkdwn": "true",
            "channel": channel_id,
            "text": text,
        }
    )
    r = requests.post("https://slack.com/api/chat.postMessage", data=params)
    r.raise_for_status()
    if r.json()["ok"] is False:
        raise ValueError(r.json().get("error", "Requests error"))
    return r


weekday_schedule = CronSchedule("30 13 * * 1-5")
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


with Flow("dc-standup-reminder", schedule=weekday_schedule, environment=env) as flow:
    updates = get_latest_updates(get_standup_date)
    res = send_reminder.map(is_reminder_needed.map(get_team, unmapped(updates)))
