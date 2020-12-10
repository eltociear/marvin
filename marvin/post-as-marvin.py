from starlette.requests import Request
from starlette.responses import Response
from .utilities import say


from .users import get_all_users


async def post_as_marvin_handler(request: Request) -> JSONResponse:
    """
    Posts a message to any channel as Marvin
    """
    try:
        payload = await request.json()
    except:
        payload = await request.form()

    text = payload.get("text")

    channel_capture_prepositions = ["in", "to"]
    last_index = -1

    for prep in channel_capture_prepositions:
        index = text.rfind(prep)

        last_index = index if index > last_index else last_index

    message = text[0:last_index].strip()
    channel = message[
        last_index + 2 :
    ].strip()  # Removes the preposition (which are all 2 characters atm)

    if not channel or last_index == -1:
        return Response(
            {
                "response_type": "ephemeral",
                "text": f"Incredible. It’s even worse than I thought it would be... Tell me where you want to post your message by including the channel in your message. /post-as-marvin <message> in #<channel>",
            }
        )

    # Post the message to the described channel
    say(message, channel=channel)

    # Respond (ephemerally) to the user to confirm that the message was sent
    return Response(
        {
            "response_type": "ephemeral",
            "text": f"This is the sort of thing you lifeforms enjoy, is it? Fine, I've posted \"{message}\" to {channel}. I hope you're happy.",
        }
    )