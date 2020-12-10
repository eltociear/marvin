from starlette.requests import Request
from starlette.responses import JSONResponse

from .users import get_all_users


async def post_as_marvin_handler(request: Request) -> JSONResponse:
    """
    Posts a message to any channel as Marvin
    """
    payload = await request.form()
    text = payload.get("text")

    return JSONResponse({"response_type": "in_channel", "text": f"{text}"})
