import docker
import prefect
from prefect import Flow, Parameter, task
from prefect.client import Secret
from prefect.executors import LocalExecutor
from prefect.environments.storage import Docker
from prefect.schedules import clocks, Schedule
from prefect.engine.signals import SKIP
from prefect.utilities.tasks import unmapped

import datetime
import google.cloud.firestore
import json
import pendulum
import requests


@task
def get_standup_date():
    date_format = "%Y-%m-%d"
    now = prefect.context["scheduled_start_time"]
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
    user_dict = {
        doc.id.lower(): (doc.to_dict() or {}).get("updates") for doc in updates
    }
    return user_dict


@task
def get_team(zone):
    """
    Retrieve all current full-time Slack users.

    Returns:
        - a list of (user name, Slack User ID) tuples
    """
    client = google.cloud.firestore.Client(project="prefect-marvin")
    collection = client.collection(f"users")
    users = [u.to_dict() for u in collection.get()]
    return [
        (u["name"], u["slack"])
        for u in users
        if u["zone"] == zone and u.get("standup") is True
    ]


@task(task_run_name=lambda **kwargs: kwargs["user_info"][0])
def is_reminder_needed(user_info, current_updates):
    user_name, user_id = user_info
    if current_updates.get(user_name.lower()) is not None:
        raise SKIP(f"{user_name} has already provided an update")
    else:
        return user_info


@task()
def send_reminder(user_info):
    user_name, user_id = user_info
    TOKEN = Secret("MARVIN_TOKEN").get()

    ## get private channel ID for this user
    params = {"token": TOKEN, "users": user_id}
    r = requests.post("https://slack.com/api/conversations.open", data=params)
    channel_id = json.loads(r.text)["channel"]["id"]

    params.pop("users")
    text = (
        f"Hi {user_name}! I haven't gotten your midweek update yet; what updates do you have for the team? Please respond by using the slash command `/standup`, and remember: your response will be shared!",
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
    return user_name


zones = {
    "Eastern": "US/Eastern",
    "Central": "US/Central",
    "Mountain": "US/Mountain",
    "Pacific": "US/Pacific",
    "Alaska": "US/Alaska",
    "Hawaii": "US/Hawaii",
}
schedule_clocks = []

# We use the same cron string with a start date in different
# timezones for each coast
for key, value in zones.items():
    schedule_clocks.append(
        clocks.CronClock(
            "30 17 * * 2",
            start_date=pendulum.parse("2017-03-24", tz=value),
            parameter_defaults={"zone": key},
        )
    )

weekday_schedule = Schedule(clocks=schedule_clocks)


with Flow(
    "Standup Reminder",
    schedule=weekday_schedule,
    executor=LocalExecutor(),
) as flow:
    zone = Parameter("zone")
    updates = get_latest_updates(get_standup_date)
    team = get_team(zone)
    res = send_reminder.map(is_reminder_needed.map(team, unmapped(updates)))

flow.set_reference_tasks([res])


if __name__ == "__main__":
    default_client = docker.from_env()
    storage = Docker(
        base_url=default_client.api.base_url,
        tls_config=docker.TLSConfig(default_client.api.cert),
        registry_url="gcr.io/prefect-tenant-0c5400/flows/",
        image_name="standup-reminder-flow",
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
