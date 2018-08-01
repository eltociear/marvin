import asyncio
import logging

from .standup import scheduler


class SchedulerPolicy(asyncio.DefaultEventLoopPolicy):
    def new_event_loop(self):
        """Override new_event_loop to allow for including arbitrary coroutines
        into the uvicorn event loop.
        """
        loop = super().new_event_loop()
        asyncio.ensure_future(scheduler(), loop=loop)
        logging.getLogger("asyncio").info("New asyncio event loop created")
        return loop
