import asyncio
import datetime
import pytest
import schedule
from unittest.mock import MagicMock
from marvin import standup


@pytest.fixture(autouse=True)
def clear_schedule():
    "Fixture for clearing the global schedule after every test."
    yield
    schedule.clear()


def test_standup_is_scheduled(app, token):
    # required to prime the asyncio loop
    asyncio.ensure_future(standup.scheduler())
    app.post('/', json={'token': token})

    jobs = schedule.jobs
    assert len(jobs) == 2
    assert jobs[0].next_run.hour == 13  # pre-standup
    assert jobs[1].next_run.hour == 14  # post-standup


@pytest.mark.parametrize(
    "now", [datetime.datetime(2018, 7, 14), datetime.datetime(2018, 7, 15)]
)
def test_standup_takes_the_weekend_off(app, monkeypatch, token, now):
    # required to prime the asyncio loop
    asyncio.ensure_future(standup.scheduler())
    app.post('/', json={'token': token})
    say = MagicMock()
    monkeypatch.setattr(standup, 'say', say)

    pre, post = schedule.jobs
    pre.next_run = now
    post.next_run = now

    class date:
        @classmethod
        def now(cls):
            return now

    monkeypatch.setattr(datetime, "datetime", date)
    schedule.run_all()

    assert say.call_count == 0


def test_standup_queries_users(app, monkeypatch, token):
    monkeypatch.setattr(standup, 'get_users', lambda *args, **kwargs: {"chris": "999"})
    monkeypatch.setattr(standup, 'get_dm_channel_id', lambda *args, **kwargs: "dm_chris")
    asyncio.ensure_future(standup.scheduler())
    app.post('/', json={'token': token})

    say = MagicMock()
    monkeypatch.setattr(standup, 'say', say)

    pre, post = schedule.jobs
    pre.next_run = datetime.datetime.now()
    schedule.run_all()
    assert say.call_count == 2

    dm_msg = "Hi chris! I haven't heard from you yet; what updates do you have for the team today? Please respond by using the slash command `/standup`,  and remember: your response will be shared!"
    pub_msg = "<!here> are today's standup updates"
    assert say.call_args_list[0][0][0] == dm_msg
    assert pub_msg in say.call_args_list[1][0][0]
