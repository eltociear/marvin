import asyncio
import json
import logging
import os
import uvicorn

from apistar import ASyncApp, Route
from apistar.http import Body

from .responses import event_handler, version_handler
from .standup import scheduler, standup_handler


VALIDATION_TOKEN = os.environ.get('SLACK_VALIDATION_TOKEN')
logging.getLogger('asyncio').setLevel(logging.INFO)


class TokenVerificationHook:
    def on_request(self, data: Body):
        try:
            payload = json.loads(data)
            token = payload.get('token', '')
        except json.JSONDecodeError:
            data = data.decode()
            token = [t.split('=')[1] for t in data.split('&') if t.startswith('token')][0]
        assert token == VALIDATION_TOKEN, 'Token Authentication Failed'


MarvinApp = ASyncApp(routes=[
                             Route('/standup', method='POST', handler=standup_handler),
                             Route('/version', method='POST', handler=version_handler),
                             Route('/', method='POST', handler=event_handler)],
               event_hooks=[TokenVerificationHook])


def run():
    asyncio.ensure_future(scheduler())
    uvicorn.run(MarvinApp, '0.0.0.0', 8080, log_level="info", loop='asyncio')


if __name__ == "__main__":
    run()
