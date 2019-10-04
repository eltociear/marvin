import asyncio
import json
import re

from starlette.requests import Request
from starlette.responses import Response

from .utilities import say

from .firestore import client


async def leaderboard_handler(request: Request) -> Response:
    payload = await request.form()
    update = payload.get("text")
    channel = payload.get("channel_id")

    # logic for making google query
    top_match = re.compile("^top($|\s)(\d*)\s*$").match(update)
    bottom_match = re.compile("^bottom($|\s)(\d*)\s*$").match(update)
    count_match = re.compile("(^\d*)\s*$").match(update)

    if top_match:
        count = int(top_match.groups()[-1].strip())
        direction = google.cloud.firestore.Query.DESCENDING
        query = (
            client.collection("karma")
            .order_by("value", direction=direction)
            .limit(count + 2)
        )
        results = [
            (d.id, d.get("value"))
            for d in query.get()
            if d.id not in ("marvin", "easter egg")
        ]
    elif count_match:
        count = int(count_match.groups()[0].strip())
        direction = google.cloud.firestore.Query.DESCENDING
        query = (
            client.collection("karma")
            .order_by("value", direction=direction)
            .limit(count + 2)
        )
        results = [
            (d.id, d.get("value"))
            for d in query.get()
            if d.id not in ("marvin", "easter egg")
        ]
    elif bottom_match:
        count = int(bottom_match.groups()[-1].strip())
        direction = google.cloud.firestore.Query.ASCENDING
        query = (
            client.collection("karma")
            .order_by("value", direction=direction)
            .limit(count)
        )
        results = [(d.id, d.get("value")) for d in query.get()]

    msg = "The leaderboard results are:\n\n"

    for name, votes in results:
        msg += f"- {name}: {votes}\n"

    say(msg, channel=channel)
    return Response()
