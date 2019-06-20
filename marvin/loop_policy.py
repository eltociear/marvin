import asyncio
import logging
import pendulum
import schedule
import marvin.standup
import marvin.responses
import marvin.utilities

from prefect import Client


ALERT_CHANNEL = "CK9RY9J3C"
STAGING_QUERY = (
    """
query{
  flow(where: {name: {_eq: "BE: Slightly Longer Sleeper in Stg"}}){
    flow_runs(where: {scheduled_start_time: {_gte: \""""
    + pendulum.now("utc").add(minutes=-5).isoformat()
    + """\"}, state: {_eq: "Success"}}){
      state
    }
  }
}
"""
)


async def ping_staging():
    while True:
        c = Client()
        try:
            result = c.graphql(STAGING_QUERY)
            assert result.data.flow, "Flow does not appear to exist!"
            assert result.data.flow[0].flow_runs, "No successful flow runs found!"
            assert (
                result.data.flow[0].flow_runs[0].state == "Success"
            ), "No successful flow runs found!"
        except AssertionError as exc:
            msg = f"Staging might be down: check your flows!  I tried to query for successful flow runs but got:\n ```{repr(exc)}```"
            marvin.utilities.say(msg, channel=ALERT_CHANNEL)
        except Exception as exc:
            msg = f"Staging is down!  I tried to connect but got:\n ```{repr(exc)}```"
            marvin.utilities.say(msg, channel=ALERT_CHANNEL)

        await asyncio.sleep(5 * 60)  # 5 minutes


async def run_scheduler(ignore_google=False, ignore_standup=True):
    """
    Create schedules, then look for scheduled jobs every 5 seconds.
    """
    if not ignore_standup:
        await marvin.standup.schedule_standup()
    if not ignore_google:
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
        asyncio.ensure_future(ping_staging(), loop=loop)
        logging.getLogger("asyncio").info("New asyncio event loop created")
        return loop
