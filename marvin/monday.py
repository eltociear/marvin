import requests
import os

from starlette.requests import Request
from starlette.responses import Response
from .utilities import say

headers = {"Authorization": os.getenv("MONDAY_API_TOKEN")}


async def monday_handler_backlog(request: Request):
    board_id = 517793474
    group_id = "inbox"
    slack_data = await extract_data(request)
    monday_handler(slack_data, board_id, group_id)
    username = slack_data["username"]
    text = slack_data["text"]
    notify_channel_text = (
        f"{username} just added '{text}' to the product backlog in Monday"
    )
    say(notify_channel_text, channel="CBH18KG8G")
    return Response(
        "It gives me a headache just trying to think down to your level, but I have added this to the product backlog."
    )


async def monday_handler_blogs(request: Request):
    board_id = 774900963
    group_id = "topics"
    slack_data = await extract_data(request)
    monday_handler(slack_data, board_id, group_id)
    username = slack_data["username"]
    text = slack_data["text"]
    notify_channel_text = f"{username} just added '{text}' to the blog list in Monday"
    say(notify_channel_text, channel="CBH18KG8G")
    return Response(
        "It gives me a headache just trying to think down to your level, but I have added this to Monday."
    )


async def monday_handler_customer_feedback(request: Request):
    board_id = 585522431
    group_id = "new_group93191"
    slack_data = await extract_data(request)
    monday_handler(slack_data, board_id, group_id)
    return Response(
        "It gives me a headache just trying to think down to your level, but I have added this to Monday."
    )


async def monday_handler_prefect_on_prefect(request: Request):
    board_id = 907275859
    group_id = "topics"
    slack_data = await extract_data(request)
    monday_handler(slack_data, board_id, group_id)
    username = slack_data["username"]
    text = slack_data["text"]
    notify_channel_text = f"{username} just added '{text}' to the Prefect-on-Prefect laundry basket in Monday"
    # notifies the general channel
    say(notify_channel_text, channel="CANLZB1L3")
    return Response(
        "It gives me a headache just trying to think down to your level, but I have added this to Monday."
    )


async def monday_handler_any_board(request: Request):
    # provide the board id followed by a ' ' and then the text you want added to the board
    # for example "585522431 a new item to add to the monday board"
    # by default the first group created in any board is called 'topics' and will automatically add items to that group
    slack_data = await extract_data(request)
    text = slack_data["text"] or ""
    try:
        board_id = int(text.split(" ", 1)[0])
    except ValueError:
        return Response(
            "A valid board id has not been provided. Try again with the board id followed by a space."
        )
    group_id = "topics"
    new_text = text.split(" ", 1)[1]
    slack_data["text"] = new_text
    slack_data["text_summary"] = (
        (new_text[:60] + "...") if len(new_text) > 60 else new_text
    )
    monday_handler(slack_data, board_id, group_id)
    return Response(
        "It gives me a headache just trying to think down to your level, but I have added this to Monday."
    )


def monday_handler(slack_data, board_id, group_id):
    result = create_item(board_id, group_id, slack_data["text_summary"])
    get_id_result = get_create_item_id(result)
    create_update(
        get_id_result, slack_data["text"], slack_data["username"], slack_data["channel"]
    )


async def extract_data(request: Request):
    payload = await request.form()
    text = payload.get("text")
    text_summary = (text[:60] + "...") if len(text) > 60 else text
    username = payload.get("user_name")
    channel = payload.get("channel_name")
    return {
        "text": text,
        "text_summary": text_summary,
        "username": username,
        "channel": channel,
    }


def create_item(board_id, group_id, text_summary):
    variables = {
        "MONDAY_BOARD_ID": board_id,
        "MONDAY_GROUP_ID": group_id,
        "TEXT_SUMMARY": text_summary,
    }

    query = """
        mutation ($MONDAY_BOARD_ID:Int!, $MONDAY_GROUP_ID:String!, $TEXT_SUMMARY:String!) {
            create_item (board_id: $MONDAY_BOARD_ID, group_id: $MONDAY_GROUP_ID, item_name: $TEXT_SUMMARY)
            {
                id
            }
        }
    """

    response = requests.post(
        "https://api.monday.com/v2/",
        json={"query": query, "variables": variables},
        headers=headers,
    )
    response.raise_for_status()
    return response.json()


def get_create_item_id(data):
    return data["data"]["create_item"]["id"]


def create_update(item_id, text, username, channel):
    body = f"username: {username} in channel {channel} added {text}"

    variables = {"item_id": int(item_id), "body": body}

    query = """
    mutation ($item_id:Int!, $body:String!) {
        create_update (item_id: $item_id, body: $body) {
            id
        }
    }
    """

    response = requests.post(
        "https://api.monday.com/v2/",
        json={"query": query, "variables": variables},
        headers=headers,
    )
    response.raise_for_status()
