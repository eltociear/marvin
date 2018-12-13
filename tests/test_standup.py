import asyncio
import datetime
import pytest
import schedule
from unittest.mock import MagicMock
from marvin import standup
from marvin import loop_policy


@pytest.fixture(autouse=True)
def clear_schedule():
    "Fixture for clearing the global schedule after every test."
    yield
    schedule.clear()


def get_pre_post_jobs():
    "Utility for retrieveing the _pre_standup and _post_standup jobs"
    pre = next(j for j in schedule.jobs if j.job_func.__name__ == "_pre_standup")
    post = next(j for j in schedule.jobs if j.job_func.__name__ == "_post_standup")
    return pre, post


def test_standup_is_scheduled(app, token):
    # required to prime the asyncio loop
    asyncio.ensure_future(loop_policy.run_scheduler(ignore_google=True))
    app.post("/", json={"token": token})

    pre, post = get_pre_post_jobs()
    assert pre.next_run.hour == 13
    assert post.next_run.hour == 14


@pytest.mark.parametrize(
    "now", [datetime.datetime(2018, 7, 14), datetime.datetime(2018, 7, 15)]
)
def test_standup_takes_the_weekend_off(app, monkeypatch, token, now):
    # required to prime the asyncio loop
    asyncio.ensure_future(loop_policy.run_scheduler(ignore_google=True))
    app.post("/", json={"token": token})
    say = MagicMock()
    monkeypatch.setattr(standup, "say", say)

    pre, post = get_pre_post_jobs()
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
    monkeypatch.setattr(standup, "get_users", lambda *args, **kwargs: {"chris": "999"})
    monkeypatch.setattr(
        standup, "get_dm_channel_id", lambda *args, **kwargs: "dm_chris"
    )
    asyncio.ensure_future(loop_policy.run_scheduler(ignore_google=True))
    app.post("/", json={"token": token})

    say = MagicMock()
    monkeypatch.setattr(standup, "say", say)
    monkeypatch.setattr(standup, "_is_weekday", lambda: True)

    pre, post = get_pre_post_jobs()
    pre.next_run = datetime.datetime.now()
    schedule.run_all()
    assert say.call_count == 2

    dm_msg = "Hi chris! I haven't heard from you yet; what updates do you have for the team today? Please respond by using the slash command `/standup`,  and remember: your response will be shared!"
    pub_msg = "<!here> are today's standup updates"
    assert say.call_args_list[0][0][0] == dm_msg
    assert pub_msg in say.call_args_list[1][0][0]


def test_standup_stores_updates(app, monkeypatch, token):
    # required to prime the asyncio loop
    asyncio.ensure_future(loop_policy.run_scheduler(ignore_google=True))
    say = MagicMock()
    monkeypatch.setattr(standup, "say", say)

    r = app.post(
        "/standup", json={"token": token, "user_name": "test-user", "text": "not much"}
    )
    assert r.ok
    assert r.text == "Thanks test-user!"
    assert standup.UPDATES == {"test-user": "not much\n"}
    standup.UPDATES.clear()


def test_standup_has_a_clear_feature(app, monkeypatch, token):
    # required to prime the asyncio loop
    asyncio.ensure_future(loop_policy.run_scheduler(ignore_google=True))
    say = MagicMock()
    monkeypatch.setattr(standup, "say", say)

    r = app.post(
        "/standup", json={"token": token, "user_name": "test-user", "text": "not much"}
    )
    r = app.post(
        "/standup",
        json={
            "token": token,
            "user_name": "test-user",
            "text": "clear and a bunch of other noise",
        },
    )
    assert r.ok
    assert r.text == "~not much~"
    assert standup.UPDATES == {}


def test_standup_has_a_clear_feature_that_doesnt_require_a_space(
    app, monkeypatch, token
):
    # required to prime the asyncio loop
    asyncio.ensure_future(loop_policy.run_scheduler(ignore_google=True))
    say = MagicMock()
    monkeypatch.setattr(standup, "say", say)

    r = app.post(
        "/standup", json={"token": token, "user_name": "test-user", "text": "not much"}
    )
    r = app.post(
        "/standup", json={"token": token, "user_name": "test-user", "text": "clear"}
    )
    assert r.ok
    assert r.text == "~not much~"
    assert standup.UPDATES == {}


def test_standup_clear_responds_even_when_nothing_to_clear(app, monkeypatch, token):
    # required to prime the asyncio loop
    asyncio.ensure_future(loop_policy.run_scheduler(ignore_google=True))
    say = MagicMock()
    monkeypatch.setattr(standup, "say", say)

    r = app.post(
        "/standup", json={"token": token, "user_name": "test-user", "text": "clear"}
    )
    assert r.ok
    assert r.text == "No updates to clear!"
    assert standup.UPDATES == {}


def test_standup_show_displays_current_status(app, monkeypatch, token):
    # required to prime the asyncio loop
    asyncio.ensure_future(loop_policy.run_scheduler(ignore_google=True))
    say = MagicMock()
    monkeypatch.setattr(standup, "say", say)

    standup.UPDATES = {"test-user": "debugging"}
    r = app.post(
        "/standup", json={"token": token, "user_name": "test-user", "text": "show"}
    )
    assert r.ok
    assert r.text == "debugging"
    standup.UPDATES.clear()


def test_standup_show_is_empty(app, monkeypatch, token):
    # required to prime the asyncio loop
    asyncio.ensure_future(loop_policy.run_scheduler(ignore_google=True))
    say = MagicMock()
    monkeypatch.setattr(standup, "say", say)

    r = app.post(
        "/standup", json={"token": token, "user_name": "test-user", "text": "show"}
    )
    assert r.ok
    assert r.text == "I haven't received any updates from you yet, test-user."
