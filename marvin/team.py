import asyncio
import json
import random
import re

import coolname
from starlette.requests import Request
from starlette.responses import Response

from .firestore import client
from .users import USERS
from .utilities import say

connectors = [
    ", hereby known as",
    ", henceforth known as",
    ", forever remembered as",
    ", who shall be called",
    ", AKA",
    ", who occaisionally moonlights as",
    ", sometimes known as",
    ", forever immortalized as",
    ", who goes by the alias",
    ", the best Prefect employee... um, I mean",
    ", hereby named",
    ", hereby called",
    ", henceforth named",
    ", henceforth called",
    ", who shall be named",
    ", who shall be known as",
    ", who shall be named",
    ", who will be called",
    ", whom I've decided to call",
    ", whom I've decided to name",
    ", or as we all prefer,",
    ", who definitely isn't",
    ", a figment of my imagination called",
    ", a collective delusion we all call",
    ", henceforth referred to as",
    ", who is now called",
    ", who is now named",
    ", who is now referred to as",
    ", who will be called",
    ", who will be named",
    ", who will be known as",
    ", who prefers to be called",
    ", who prefers to be known as",
    ", who prefers the name",
    ", who goes by",
    ", who goes by the name",
    ", who goes by the title",
    ", I knight thee",
    ", who spends weekends as",
    ", who spends Thursday nights as",
    ", who spends Tuesday afternoons from 2-4 as",
    ", whom we all know as",
    ", who shall be remembered as",
    ", or as their friends call them,",
    ", or as their enemies call them,",
    ", or as their frenemies call them,",
    ", or as their colleagues call them,",
    ", or as their book club calls them,",
    ", or as their weekend kickball league calls them,",
]
connectors.extend([""] * int(0.6 * len(connectors)))

# copied from Prefect Cloud
COOLNAME_BLACKLIST = {
    "sexy",
    "demonic",
    "kickass",
    "heretic",
    "godlike",
    "booby",
    "chubby",
    "gay",
    "sloppy",
    "funky",
    "juicy",
    "beaver",
    "curvy",
    "fat",
    "flashy",
    "flat",
    "thick",
    "nippy",
}


def generate_name() -> str:
    """
    Generates a random slug.
    """
    words = coolname.generate(2)

    # regenerate words if they include blacklisted words
    while COOLNAME_BLACKLIST.intersection(words):
        words = coolname.generate(2)

    return words


async def roundtable_order_handler(request: Request) -> Response:

    payload = await request.form()
    update = payload.get("text")
    channel = payload.get("channel_id")

    names = [u["name"] for u in USERS]

    msgs = []
    for i, name in enumerate(random.sample(names, len(names))):
        alias = " ".join(w.capitalize() for w in generate_name())
        msgs.append(f"{i+1} - *{name}*{random.choice(connectors)} *the {alias}*")
    print("\n".join(msgs))

    say("\n".join(msg), channel=channel)
    return Response()
