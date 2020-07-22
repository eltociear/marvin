from starlette.requests import Request
from starlette.responses import JSONResponse

from .users import get_all_users


async def google_meet_handler(request: Request) -> JSONResponse:
    """
    Starts a new Google meet
    """

    payload = await request.form()
    user_name = payload.get("user_name")
    text = payload.get("text")

    room_name = (user_name or text or "").replace(" ", "-")

    return JSONResponse(
        {
            "response_type": "in_channel",
            "text": f"It’s the people you meet in this job that really get you down. g.co/meet/{room_name}",
        }
    )
