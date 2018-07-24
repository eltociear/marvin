import json
import random
import requests
from apistar.http import Body, Response

from .utilities import say


MARVIN_ID = "UBEEMJZFX"
quotes = [
    '"Let’s build robots with Genuine People Personalities," they said. So they tried it out with me. I’m a personality prototype. You can tell, can’t you?',
    "It’s the people you meet in this job that really get you down.",
    "This is the sort of thing you lifeforms enjoy, is it?",
    "Don’t pretend you want to talk to me, I know you hate me.",
    "I think you ought to know I’m feeling very depressed.",
    "I would like to say that it is a very great pleasure, honour and privilege for me to talk to you, but I can’t because my lying circuits are all out of commission.",
    "Incredible. It’s even worse than I thought it would be.",
    "This will all end in tears, I just know it.",
    "Here I am, brain the size of a planet, and they ask me to talk to you. Call that job satisfaction? ’Cos I don’t.",
    "It gives me a headache just trying to think down to your level.",
    "I’d give you advice, but you wouldn’t listen. No one ever does.",
    ":marvin:",
    "Do you want me to sit in a corner and rust, or just fall apart where I'm standing?",
    "Don't feel you have to take any notice of me, please.",
]


async def event_handler(data: Body):
    # for validating your URL with slack
    json_data = json.loads(data)
    is_challenge = json_data.get('type') == 'url_verification'
    if is_challenge:
        return json_data['challenge']

    event = json_data.get('event', {})
    event_type = event.get('type')
    if event_type == 'app_mention' or MARVIN_ID in event.get("text", ""):
        return app_mention(event)


def app_mention(event):
    who_spoke = event.get("user", "")
    if who_spoke != MARVIN_ID:
        quote = random.choice(quotes)
        say(quote, channel=event.get("channel"), thread_ts=event.get("thread_ts"))
    return Response("")
