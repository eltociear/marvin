import asyncio
import json
import random
import re

import coolname
from starlette.requests import Request
from starlette.responses import Response, JSONResponse

from .users import get_all_users


async def google_meet_handler(request: Request) -> Response:
    """
    Starts a new Google meet
    """

    payload = await request.form()
    user_id = payload.get("user_id")

    users = get_all_users()
    user = next((u for u in users if u.get("slack") == user_id), {})
    meet_url = user.get("google_meet_url")
    if not meet_url:
        return Response()

    return JSONResponse({"response_type": "in_channel", "text": meet_url})
