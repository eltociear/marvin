import asyncio
import logging
import schedule
import marvin.standup
import marvin.responses


async def run_scheduler():
    """
    Create schedules, then look for scheduled jobs every 5 seconds.
    """
    await marvin.standup.schedule_standup()
    await marvin.responses.schedule_refresh_users()

    while True:
        schedule.run_pending()
        await asyncio.sleep(5)


class SchedulerPolicy(asyncio.DefaultEventLoopPolicy):
    def new_event_loop(self):
        """Override new_event_loop to allow for including arbitrary coroutines
        into the uvicorn event loop.
        """
        loop = super().new_event_loop()
        asyncio.ensure_future(run_scheduler(), loop=loop)
        logging.getLogger("asyncio").info("New asyncio event loop created")
        return loop
