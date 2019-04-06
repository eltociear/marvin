import asyncio
import hmac
import json
import logging
import os
import uvicorn

from apistar import ASyncApp, Route
from apistar.http import Body, Headers

from .github import cloud_github_handler, core_github_handler
from .loop_policy import SchedulerPolicy
from .responses import event_handler, version_handler
from .defcon import defcon_handler
from .standup import standup_handler


GITHUB_VALIDATION_TOKEN = os.environ.get("GITHUB_VALIDATION_TOKEN", "").encode()
SLACK_VALIDATION_TOKEN = os.environ.get("SLACK_VALIDATION_TOKEN")
logging.basicConfig(
    level=2,
    format="%(asctime)s %(levelname)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)


def slack_validation(data):
    try:
        payload = json.loads(data)
        token = payload.get("token", "")
    except json.JSONDecodeError:
        data = data.decode()
        token = [t.split("=")[1] for t in data.split("&") if t.startswith("token")][0]
    assert token == SLACK_VALIDATION_TOKEN, "Token Authentication Failed"


def github_validation(data, sig):
    expected = f"sha1={hmac.new(GITHUB_VALIDATION_TOKEN, msg=data, digestmod='sha1').hexdigest()}"
    assert expected == sig, "Secret Authentication Failed"


class TokenVerificationHook:
    def on_request(self, data: Body, headers: Headers):
        xhub_sig = headers.get("x-hub-signature", "")
        if xhub_sig.startswith("sha1"):
            github_validation(data, xhub_sig)
        else:
            slack_validation(data)


MarvinApp = ASyncApp(
    routes=[
        Route("/github/cloud", method="POST", handler=cloud_github_handler),
        Route("/github/core", method="POST", handler=core_github_handler),
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
