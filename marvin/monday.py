import requests
import os

from starlette.requests import Request
from starlette.responses import Response
from .utilities import say

headers = {"Authorization": os.getenv("MONDAY_API_TOKEN")}


async def monday_handler_roadmap(request: Request):
    board_id = 517793474
    group_id = "topics"
    notify_channel_text = (
        f"[username] just added '[text]' to the product laundry basket in Monday"
    )
    channel_to_notify = "CBH18KG8G"
    await monday_handler(request, board_id, group_id, notify_channel_text, channel_to_notify)
    return Response(
        "It gives me a headache just trying to think down to your level, but I have added this to Monday."
    )


async def monday_handler_blogs(request: Request):
    board_id = 774900963
    group_id = "topics"
    notify_channel_text = f"[username] just added '[text]' to the blog list in Monday"
    channel_to_notify = "CBH18KG8G"
    await monday_handler(request, board_id, group_id, notify_channel_text, channel_to_notify)
    return Response(
        "It gives me a headache just trying to think down to your level, but I have added this to Monday."
    )


async def monday_handler_customer_feedback(request: Request):
    board_id = 585522431
    group_id = "new_group93191"
    notify_channel_text = (
        f"[username] just added '[text]' to the customer feedback in Monday"
    )
    channel_to_notify = "CBH18KG8G"
    await monday_handler(request, board_id, group_id, notify_channel_text, channel_to_notify)
    return Response(
        "It gives me a headache just trying to think down to your level, but I have added this to Monday."
    )


async def monday_handler_any_board(request: Request):
    # provide the board id followed by a ' ' and then the text you want added to the board
    # for example "585522431 a new item to add to the monday board"
    # by default the first group created in any board is called 'topics' and will automatically add items to that group
    payload = await request.form()
    text = payload.get("text") or ""
    try:
        board_id = int(text.split(" ", 1)[0])
    except ValueError:
        return Response(
            "A valid board id has not been provided. Try again with the board id followed by a space."
        )
    group_id = "topics"
    await monday_handler(request, board_id, group_id)
    return Response(
        "It gives me a headache just trying to think down to your level, but I have added this to Monday."
    )


async def monday_handler(
    request: Request, board_id, group_id, notify_channel_text=None, channel_to_notify=None
):
    payload = await request.form()
    text = payload.get("text")
    username = payload.get("user_name")
    channel = payload.get("channel_name")
    result = create_item(board_id, group_id)
    get_id_result = get_create_item_id(result)
    create_update(get_id_result, text, username, channel)
    if notify_channel_text and channel_to_notify:
        notify_channel_text.replace("[username]", "{username}")
        notify_channel_text.replace("[text]", "{text}")
        notify_channel(notify_channel_text, channel_to_notify)


def notify_channel(notify_channel_text, channel_to_notify):
    say(notify_channel_text, channel=channel_to_notify)


def create_item(board_id, group_id):
    variables = {"MONDAY_BOARD_ID": board_id, "MONDAY_GROUP_ID": group_id}

    query = """
        mutation ($MONDAY_BOARD_ID:Int!, $MONDAY_GROUP_ID:String!) {
            create_item (board_id: $MONDAY_BOARD_ID, group_id: $MONDAY_GROUP_ID, item_name: "Item added from slack")
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
