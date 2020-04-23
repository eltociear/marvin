import requests

from starlette.requests import Request
from starlette.responses import Response

headers = {
    "Authorization": "MONDAY_PERSONAL_TOKEN"}

async def monday_handler(request: Request):
    payload = await request.json()
    text = payload.get("text")
    username = payload.get("username")
    channel = payload.get("channel")
    result = create_item()
    get_id_result = get_create_item_id(result)
    create_update(get_id_result, text, username, channel)
    return Response("An item has been added to ...")

def create_item():
    query = """
        mutation
        {
            create_item (board_id: 517793474, group_id: "topics", item_name: "new item added from slack")
            {
                id
            }
        }
    """

    response = requests.post('https://api.monday.com/v2/', json={'query': query}, headers=headers)
    if response.status_code == 200:
        return response.json()
    else:
        raise Exception("Query failed {}. {}".format(response.status_code, query))

def get_create_item_id(data):
    return data["data"]["create_item"]["id"]

def create_update(item_id, text, username, channel):
    body = f"username: {username} in channel {channel} added {text}"

    variables = {
        "item_id": int(item_id),
        "body": body
    }

    query = """
    mutation ($item_id:Int!, $body:String!) {
        create_update (item_id: $item_id, body: $body) {
            id
        }
    }
    """

    response = requests.post('https://api.monday.com/v2/', json={'query': query, 'variables': variables}, headers=headers)
    response.raise_for_status()