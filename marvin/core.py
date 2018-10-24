import asyncio
import json
import logging
import os
import uvicorn

from apistar import ASyncApp, Route
from apistar.http import Body

from .loop_policy import SchedulerPolicy
from .responses import event_handler, version_handler
from .defcon import defcon_handler
from .standup import standup_handler


VALIDATION_TOKEN = os.environ.get("SLACK_VALIDATION_TOKEN")
logging.basicConfig(
    level=2,
    format="%(asctime)s %(levelname)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)


class TokenVerificationHook:
    def on_request(self, data: Body):
        try:
            payload = json.loads(data)
            token = payload.get("token", "")
        except json.JSONDecodeError:
            data = data.decode()
            token = [t.split("=")[1] for t in data.split("&") if t.startswith("token")][
                0
            ]
        assert token == VALIDATION_TOKEN, "Token Authentication Failed"


MarvinApp = ASyncApp(
    routes=[
        Route("/defcon", method="POST", handler=defcon_handler),
        Route("/standup", method="POST", handler=standup_handler),
        Route("/version", method="POST", handler=version_handler),
        Route("/", method="POST", handler=event_handler),
    ],
    event_hooks=[TokenVerificationHook],
)


def run():
    asyncio.set_event_loop_policy(SchedulerPolicy())
    uvicorn.run(MarvinApp, "0.0.0.0", 8080, log_level="debug", loop="asyncio")


if __name__ == "__main__":
    run()
