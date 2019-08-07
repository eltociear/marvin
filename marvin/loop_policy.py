import asyncio
import logging
import pendulum
import schedule
import marvin.standup
import marvin.responses
import marvin.utilities

from prefect import Client


ALERT_CHANNEL = "CK9RY9J3C"


async def ping_staging():
    logger = logging.getLogger("Staging")
    logger.debug("Preparing to ping staging...")
    while True:
        c = Client()
        try:
            STAGING_QUERY = (
                """
                    query {
                     flow_run(
                      where: {
                       tenant_id: { _eq: "74aaae1e-3447-4bbd-ab83-ad6dd4e34c90" }
                       state: { _eq: "Success" }
                       end_time: {_gte: \""""
                + pendulum.now("utc").subtract(minutes=5).isoformat()
                + """\"}
                      }
                     ) {
                      state
                      end_time
                     }
                    }
            """
            )
            logger.debug(STAGING_QUERY)
            result = c.graphql(STAGING_QUERY)
            assert (
                result.data.flow_run
            ), "No successful flow runs found in the past 5 minutes!"
            logger.debug("Staging healthy.  Sleeping for 5...")
        except AssertionError as exc:
            logger.error(exc)
            msg = f"Staging might be down: check your flows!  I tried to query for successful flow runs but got:\n ```{str(exc)}```"
            marvin.utilities.say(msg, channel=ALERT_CHANNEL)
        except Exception as exc:
            logger.error(exc)
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
