import json
import logging
import os
import requests

from functools import lru_cache

from .firestore import client


MARVIN_ACCESS_TOKEN = os.environ.get("MARVIN_ACCESS_TOKEN")
OAUTH_TOKEN = os.environ.get("MARVIN_OAUTH_TOKEN")
PUBLIC_OAUTH_TOKEN = os.environ.get("MARVIN_PUBLIC_OAUTH_TOKEN")
TOKEN = os.environ.get("MARVIN_TOKEN")
PUBLIC_TOKEN = os.environ.get("MARVIN_PUBLIC_TOKEN")


async def promotional_signup(
    user_id: str = None, email: str = None, platform: str = None, link: str = None
):
    collection = client.collection(f"promotion")
    doc = dict(user_id=user_id, email=email, platform=platform, link=link)
    try:
        collection.add(document_data=doc, document_id=user_id)
    except:
        pass


def get_repo_labels(repo="cloud"):
    url = f"https://api.github.com/repos/PrefectHQ/{repo}/labels"
    headers = {"AUTHORIZATION": f"token {MARVIN_ACCESS_TOKEN}"}
    resp = requests.get(url, headers=headers)
    resp.raise_for_status()
    return json.loads(resp.text)


def get_pins(channel="CBH18KG8G"):
    """
    Retrieve all pinned items from a given channel.

    Args:
        - channel (str): the Slack Channel ID of the channel you wish to
            retrieve pins for; defaults to the ID for the #engineering channel

    Returns:
        - a list of channel "items" (see https://api.slack.com/methods/pins.list)
    """
    params = {"token": OAUTH_TOKEN, "channel": channel}
    r = requests.post("https://slack.com/api/pins.list", data=params)
    if r.ok:
        return json.loads(r.text)["items"]
    else:
        raise ValueError(f"Request failed with status code {r.status_code}")


def add_pin(channel, timestamp):
    """
    Adds a pin to a given channel.  The pinned item is specified via its timestamp.

    Args:
        - channel (str): the Slack Channel ID of the channel you will add a pin to
        - timestamp (str): the Slack Timestamp of the item you wish to pin

    Returns:
        - the requests.Request object of the POST
    """
    params = {"token": OAUTH_TOKEN, "channel": channel, "timestamp": timestamp}
    r = requests.post("https://slack.com/api/pins.add", data=params)
    return r


def remove_pin(channel, timestamp):
    """
    Removes a pin from a given channel.  The pinned item is specified via its timestamp.

    Args:
        - channel (str): the Slack Channel ID of the channel you will remove a pin from
        - timestamp (str): the Slack Timestamp of the item you wish to remove

    Returns:
        - the requests.Request object of the POST
    """
    params = {"token": OAUTH_TOKEN, "channel": channel, "timestamp": timestamp}
    r = requests.post("https://slack.com/api/pins.remove", data=params)
    return r


def get_channels():
    """
    Retrieve all currently public Prefect Slack channels.

    Returns:
        - a dictionary of channel name -> Slack Channel ID
    """
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
    """
    Retrieve all current full-time Slack users.

    Returns:
        - a dictionary of user name -> Slack User ID
    """
    params = {"token": TOKEN}
    r = requests.post("https://slack.com/api/users.list", data=params)
    if r.ok:
        user_dict = {}
        user_data = json.loads(r.text)["members"]
        for user in user_data:
            if not user["is_bot"] and user["name"] not in ("slackbot", "test-user"):
                user_dict[user["name"]] = user["id"]
        return user_dict
    else:
        return dict()


def get_dm_channel_id(userid):
    """
    Get the Slack Channel ID for Marvin's DM channel with a provided user.

    Args:
        - userid (str): the Slack User ID of the user you wish to retrieve the
            private channel for

    Returns:
        - a string of the Slack Channel ID
    """
    params = {"token": TOKEN, "users": userid}
    r = requests.post("https://slack.com/api/conversations.open", data=params)
    if r.ok:
        return json.loads(r.text)["channel"]["id"]


def public_speak(text, channel=None, **kwargs):
    """
    Utility for speaking in a given channel.

    Args:
        - text (str): what you want Marvin to say
        - channel (str): the Slack Channel ID of the channel you want Marvin to
            speak in
        - **kwargs: additional parameters to pass in the POST request

    Returns:
        - the request.Request object of the POST
    """
    params = {
        "token": PUBLIC_TOKEN,
        "as_user": "true",
        "link_names": "true",
        "mrkdwn": "true",
        "channel": channel,
        "text": text,
    }
    params.update(kwargs)
    r = requests.post("https://slack.com/api/chat.postMessage", data=params)
    return r


def say(text, channel=None, **kwargs):
    """
    Utility for speaking in a given channel.

    Args:
        - text (str): what you want Marvin to say
        - channel (str): the Slack Channel ID of the channel you want Marvin to
            speak in
        - **kwargs: additional parameters to pass in the POST request

    Returns:
        - the request.Request object of the POST
    """
    params = {
        "token": TOKEN,
        "as_user": "true",
        "link_names": "true",
        "mrkdwn": "true",
        "channel": channel,
        "text": text,
    }
    params.update(kwargs)
    r = requests.post("https://slack.com/api/chat.postMessage", data=params)
    return r


def get_public_thread(channel, ts):
    """
    Retrieve thread contents from a given thread.

    Returns:
        - a list of message "items" (see https://api.slack.com/methods/conversations.replies)
    """
    params = {"token": PUBLIC_OAUTH_TOKEN, "channel": channel, "ts": ts, "limit": 50}
    r = requests.post("https://slack.com/api/conversations.replies", data=params)
    if r.ok:
        return r.json()["messages"]
    else:
        raise ValueError(f"Request failed with status code {r.status_code}")


def get_public_message_permalink(channel, message_ts):
    """
    Retrieve message metadata.

    Returns:
        - a permalink string to the desired message (see https://api.slack.com/methods/chat.getPermalink)
    """
    params = {"token": PUBLIC_OAUTH_TOKEN, "channel": channel, "message_ts": message_ts}
    r = requests.post("https://slack.com/api/chat.getPermalink", data=params)
    if r.ok:
        return r.json()["permalink"]
    else:
        logging.error(f"Request failed with status code {r.status_code}")


@lru_cache(maxsize=1024)
def get_user_info(user, name_only=True):
    params = {"token": PUBLIC_OAUTH_TOKEN, "user": user}
    r = requests.post("https://slack.com/api/users.info", data=params)
    if r.ok:
        if name_only:
            return r.json()["user"].get("name", "unknown")
        else:
            return r.json()
    else:
        raise ValueError(f"Request failed with status code {r.status_code}")
