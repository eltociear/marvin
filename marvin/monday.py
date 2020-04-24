import requests
import os

from starlette.requests import Request
from starlette.responses import Response

headers = {"Authorization": os.getenv("MONDAY_API_TOKEN")}
MONDAY_BOARD_ID = 517793474
MONDAY_GROUP_ID = 'topics'

async def monday_handler(request: Request):
    payload = await request.form()
    text = payload.get("text")
    username = payload.get("username")
    channel = payload.get("channel")
    result = create_item()
    get_id_result = get_create_item_id(result)
    create_update(get_id_result, text, username, channel)
    return Response("It gives me a headache just trying to think down to your level, but I have added this to Monday.")

def create_item():
    variables = {"MONDAY_BOARD_ID": MONDAY_BOARD_ID, "MONDAY_GROUP_ID": MONDAY_GROUP_ID}

    query = """
        mutation ($MONDAY_BOARD_ID:Int!, $MONDAY_GROUP_ID:String!) {
            create_item (board_id: $MONDAY_BOARD_ID, group_id: $MONDAY_GROUP_ID, item_name: "Item added from slack")
            {
                id
            }
        }
    """

    response = requests.post(
        "https://api.monday.com/v2/", json={"query": query, "variables": variables}, headers=headers
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
