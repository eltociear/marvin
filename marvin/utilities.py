import json
import os
import requests


TOKEN = os.environ.get("MARVIN_TOKEN")


def get_users():
    params = {"token": TOKEN}
    r = requests.post("https://slack.com/api/users.list", data=params)
    if r.ok:
        user_dict = {}
        user_data = json.loads(r.text)["members"]
        for user in user_data:
            if not user["is_bot"] and user["name"] != "slackbot":
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
