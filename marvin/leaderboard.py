import asyncio
import json
import re

import google.cloud
from starlette.requests import Request
from starlette.responses import Response

from .firestore import client
from .utilities import say, logger


async def leaderboard_handler(request: Request) -> Response:
    payload = await request.form()
    update = payload.get("text")
    channel = payload.get("channel_id")

    # logic for making google query
    top_match = re.compile(r"^top($|\s)(\d*)\s*$").match(update)
    bottom_match = re.compile(r"^bottom($|\s)(\d*)\s*$").match(update)
    count_match = re.compile(r"(^\d*)\s*$").match(update)

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
    elif bottom_match:
        count = int(bottom_match.groups()[-1].strip())
        direction = google.cloud.firestore.Query.ASCENDING
        query = (
            client.collection("karma")
            .order_by("value", direction=direction)
            .limit(count)
        )
        results = [(d.id, d.get("value")) for d in query.get()]
    else:
        if count_match:
            try:
                count = int(count_match.groups()[0].strip())
            except Exception as e:
                logger.debug(e, exc_info=True)
                logger.debug("setting count to 10")
                count = 10
        else:
            count = 10
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
    msg = "The leaderboard results are:\n\n"

    for name, votes in results:
        msg += f"- {name}: {votes}\n"

    say(msg, channel=channel)
    return Response()
