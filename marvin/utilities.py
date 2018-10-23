import json
import os
import requests


OAUTH_TOKEN = os.environ.get("MARVIN_OAUTH_TOKEN")
TOKEN = os.environ.get("MARVIN_TOKEN")


def get_pins(channel="CBH18KG8G"):
    params = {"token": OAUTH_TOKEN, "channel": channel}
    r = requests.post("https://slack.com/api/pins.list", data=params)
    if r.ok:
        return json.loads(r.text)["items"]
    else:
        raise ValueError(f"Request failed with status code {r.status_code}")


def add_pin(channel, timestamp):
    params = {"token": OAUTH_TOKEN, "channel": channel, "timestamp": timestamp}
    r = requests.post("https://slack.com/api/pins.add", data=params)
    return r


def remove_pin(channel, timestamp):
    params = {"token": OAUTH_TOKEN, "channel": channel, "timestamp": timestamp}
    r = requests.post("https://slack.com/api/pins.remove", data=params)
    return r


def get_channels():
    params = {"token": TOKEN}
    r = requests.post("https://slack.com/api/channels.list", data=params)
    if r.ok:
        channel_dict = {}
        channel_data = json.loads(r.text)["channels"]
        for channel in channel_data:
            channel_dict[channel["name"]] = channel["id"]
        return channel_dict
    else:
        return dict()


def get_users():
    params = {"token": TOKEN}
    r = requests.post("https://slack.com/api/users.list", data=params)
    if r.ok:
        user_dict = {}
        user_data = json.loads(r.text)["members"]
        for user in user_data:
            if (
                not user["is_bot"]
                and user["name"] not in ("slackbot", "test-user")
                and not user["is_ultra_restricted"]
            ):
                user_dict[user["name"]] = user["id"]
        return user_dict
    else:
        return dict()


def get_dm_channel_id(userid):
    params = {"token": TOKEN, "user": userid}
    r = requests.post("https://slack.com/api/im.open", data=params)
    if r.ok:
        return json.loads(r.text)["channel"]["id"]


def say(text, channel=None, **kwargs):
    "Utility for speaking"
    params = {
        "token": TOKEN,
        "as_user": "true",
        "mrkdwn": "true",
        "channel": channel,
        "text": text,
    }
    params.update(kwargs)
    r = requests.post("https://slack.com/api/chat.postMessage", data=params)
    return r
