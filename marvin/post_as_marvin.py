from starlette.requests import Request
from starlette.responses import JSONResponse
from .utilities import logger, say, get_channel_id_by_name


async def post_as_marvin_handler(request: Request) -> JSONResponse:
    """
    Posts a message to any channel as Marvin
    """

    command_template = "/post-as-marvin <message> in #<channel>"

    try:
        payload = await request.json()
    except:
        payload = await request.form()

    logger.info(payload)

    text = payload.get("text")
    user = payload.get("user_name")

    channel_capture_prepositions = ["in", "to"]
    last_index = -1

    for prep in channel_capture_prepositions:
        index = text.rfind(prep)

        last_index = index if index > last_index else last_index

    message = text[:last_index].strip()
    channel_name = text[last_index + 2 :].strip()
    channel = get_channel_id_by_name(
        channel_name
    )  # Removes the preposition (which are all 2 characters atm)

    if not message:
        return JSONResponse(
            {
                "response_type": "ephemeral",
                "text": f"Don’t pretend you want to talk to me, I know you hate me... or at least tell me what you want to post by including a message. {command_template}",
            }
        )

    if not channel or last_index == -1:
        return JSONResponse(
            {
                "response_type": "ephemeral",
                "text": f"Incredible. It’s even worse than I thought it would be... Tell me where you want to post your message by including the channel in your message. {command_template}",
            }
        )

    logger.info(
        f"{user} posted the following message to {channel_name} as Marvin: '{message}'"
    )

    # Post the message to the described channel
    say(message, channel=channel)

    # Respond (ephemerally) to the user to confirm that the message was sent
    return JSONResponse(
        {
            "response_type": "ephemeral",
            "text": f"This is the sort of thing you lifeforms enjoy, is it? Fine, I've posted \"{message}\" to {channel_name}. I hope you're happy.",
        }
    )
