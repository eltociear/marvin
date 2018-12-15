import json
import os
import requests


OAUTH_TOKEN = os.environ.get("MARVIN_OAUTH_TOKEN")
TOKEN = os.environ.get("MARVIN_TOKEN")


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
    """
    Get the Slack Channel ID for Marvin's DM channel with a provided user.

    Args:
        - userid (str): the Slack User ID of the user you wish to retrieve the
            private channel for

    Returns:
        - a string of the Slack Channel ID
    """
    params = {"token": TOKEN, "user": userid}
    r = requests.post("https://slack.com/api/im.open", data=params)
    if r.ok:
        return json.loads(r.text)["channel"]["id"]


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
