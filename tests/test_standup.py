import datetime
import pytest
import schedule

from marvin.standup import Standup


@pytest.fixture(autouse=True)
def clear_schedule():
    "Fixture for clearing the global schedule after every test."
    yield
    schedule.clear()


def test_standup_schedules(slack):
    standup = Standup(slack)
    jobs = schedule.jobs
    assert len(jobs) == 2
    assert jobs[0].next_run.hour == 13 # pre-standup
    assert jobs[1].next_run.hour == 14 # post-standup


@pytest.mark.parametrize("now", [datetime.datetime(2018, 7, 14),
                            datetime.datetime(2018, 7, 15)])
def test_standup_takes_the_weekend_off(slack, monkeypatch, now):
    standup = Standup(slack)
    pre, post = schedule.jobs
    pre.next_run = now
    post.next_run = now

    class date:
        @classmethod
        def now(cls):
            return now

    monkeypatch.setattr(datetime, 'datetime', date)
    schedule.run_all()

    assert slack.api_not_called()


def test_standup_queries_users(slack):
    standup = Standup(slack)
    standup.get_users = lambda *args, **kwargs: {'chris': '999'}
    standup.get_dm_channel_id = lambda *args, **kwargs: 'dm_chris'
    pre, post = schedule.jobs
    pre.next_run = datetime.datetime.now()
    schedule.run_all()
    msg = "Hi chris! What updates do you have for the team today? Please respond by threading to this message and remember: your response will be shared!"
    assert slack.api_called_with('chat.postMessage', text=msg, channel='dm_chris')
