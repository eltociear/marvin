import asyncio
import hmac
import json
import logging
import os
import urllib

import uvicorn
from starlette.applications import Starlette
from starlette.requests import Request
from starlette.routing import Route

from .defcon import defcon_handler
from .github import cloud_github_handler, core_github_handler
from .leaderboard import leaderboard_handler
from .loop_policy import ping_staging, run_scheduler
from .responses import event_handler, public_event_handler, version_handler
from .standup import standup_handler
from .team import roundtable_order_handler
from .meet import google_meet_handler
from .monday import monday_handler

GITHUB_VALIDATION_TOKEN = os.environ.get("GITHUB_VALIDATION_TOKEN", "").encode()
SLACK_VALIDATION_TOKEN = os.environ.get("SLACK_VALIDATION_TOKEN")
PUBLIC_VALIDATION_TOKEN = os.environ.get("PUBLIC_VALIDATION_TOKEN")

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
        data = urllib.parse.parse_qs(data.decode())
        token = data.get("token")[0]
    assert token in [
        PUBLIC_VALIDATION_TOKEN,
        SLACK_VALIDATION_TOKEN,
    ], "Token Authentication Failed"


def github_validation(data, sig):
    expected = f"sha1={hmac.new(GITHUB_VALIDATION_TOKEN, msg=data, digestmod='sha1').hexdigest()}"
    assert expected == sig, "Secret Authentication Failed"


def check_token(fn):
    """
    Check signatures on every request

    Note: this should be a middleware, but Starlette does not allow middleware to access
    the request body. Therefore, we write it as a decorator and apply it to each route.
    """

    async def token_verification(request: Request):
        xhub_sig = request.headers.get("x-hub-signature", "")
        body = await request.body()
        if xhub_sig.startswith("sha1"):
            github_validation(body, xhub_sig)
        else:
            slack_validation(body)
        return await fn(request)

    return token_verification


MarvinApp = Starlette()

MarvinApp.add_route("/meet", check_token(google_meet_handler), methods=["POST"])
MarvinApp.add_route("/monday", check_token(monday_handler), methods=["POST"])
MarvinApp.add_route(
    "/github/cloud", check_token(cloud_github_handler), methods=["POST"]
)
MarvinApp.add_route("/github/core", check_token(core_github_handler), methods=["POST"])
MarvinApp.add_route("/defcon", check_token(defcon_handler), methods=["POST"])
MarvinApp.add_route("/leaderboard", check_token(leaderboard_handler), methods=["POST"])
MarvinApp.add_route(
    "/roundtable-order", check_token(roundtable_order_handler), methods=["POST"]
)
MarvinApp.add_route("/standup", check_token(standup_handler), methods=["POST"])
MarvinApp.add_route("/version", check_token(version_handler), methods=["POST"])
MarvinApp.add_route("/public", check_token(public_event_handler), methods=["POST"])
MarvinApp.add_route("/", check_token(event_handler), methods=["POST"])


@MarvinApp.on_event("startup")
async def run_scheduled_events():
    asyncio.create_task(run_scheduler())
    #    asyncio.create_task(ping_staging())
    await asyncio.sleep(0.0001)


def run():
    uvicorn.run(MarvinApp, host="0.0.0.0", port=8080, log_level="debug", loop="asyncio")


if __name__ == "__main__":
    run()
