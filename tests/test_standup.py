import asyncio
import datetime
from unittest.mock import MagicMock
from urllib.parse import urlencode

import pytest
import schedule

from marvin import loop_policy, standup


@pytest.mark.parametrize(
    "now,collection",
    [
        (datetime.datetime(2018, 7, 13, 0), "2018-07-13"),
        (datetime.datetime(2018, 7, 13, 14, 5), "2018-07-16"),
        (datetime.datetime(2018, 7, 14, 0), "2018-07-16"),
        (datetime.datetime(2018, 7, 15, 0), "2018-07-16"),
        (datetime.datetime(2018, 7, 16, 0), "2018-07-16"),
        (datetime.datetime(2018, 7, 16, 14, 5), "2018-07-17"),
        (datetime.datetime(2018, 7, 17, 14, 0), "2018-07-17"),
        (datetime.datetime(2018, 7, 17, 14, 1), "2018-07-17"),
        (datetime.datetime(2018, 7, 17, 14, 2), "2018-07-18"),
        (datetime.datetime(2018, 12, 25, 5, 20, 55, 592853), "2018-12-25"),
    ],
)
async def test_standup_identifies_the_right_date_an_update_belongs_to(
    monkeypatch, now, collection
):
    class date:
        @classmethod
        def utcnow(cls):
            return now

    monkeypatch.setattr(datetime, "datetime", date)
    assert standup.get_collection_name() == collection


async def test_standup_stores_updates(app, monkeypatch, token):

    say = MagicMock()
    updates = MagicMock()
    monkeypatch.setattr(standup, "say", say)
    monkeypatch.setattr(standup, "update_user_updates", updates)

    r = await app.post(
        "/standup",
        data={"token": token, "user_name": "test-user", "text": "not much"},
        headers={"Content-type": "application/x-www-form-urlencoded"},
    )
    assert r.ok
    assert r.text == "Thanks test-user!"
    assert updates.call_args[0] == ("test-user", "not much")


async def test_standup_has_a_clear_feature(app, monkeypatch, token):

    say = MagicMock()
    clear = MagicMock(return_value="not much")
    monkeypatch.setattr(standup, "say", say)
    monkeypatch.setattr(standup, "pop_user_updates", clear)

    r = await app.post(
        "/standup",
        data={"token": token, "user_name": "test-user", "text": "not much"},
        headers={"Content-type": "application/x-www-form-urlencoded"},
    )
    r = await app.post(
        "/standup",
        data={
            "token": token,
            "user_name": "test-user",
            "text": "clear and a bunch of other noise",
        },
        headers={"Content-type": "application/x-www-form-urlencoded"},
    )
    assert r.ok
    assert r.text == "~not much~"
    assert clear.call_args[0] == ("test-user",)


async def test_standup_has_a_clear_feature_that_doesnt_require_a_space(
    app, monkeypatch, token
):

    say = MagicMock()
    clear = MagicMock(return_value="not much")
    monkeypatch.setattr(standup, "say", say)
    monkeypatch.setattr(standup, "pop_user_updates", clear)

    r = await app.post(
        "/standup",
        data={"token": token, "user_name": "test-user", "text": "not much"},
        headers={"Content-type": "application/x-www-form-urlencoded"},
    )
    r = await app.post(
        "/standup",
        data={"token": token, "user_name": "test-user", "text": "clear"},
        headers={"Content-type": "application/x-www-form-urlencoded"},
    )
    assert r.ok
    assert r.text == "~not much~"
    assert clear.call_args[0] == ("test-user",)


async def test_standup_clear_responds_even_when_nothing_to_clear(
    app, monkeypatch, token
):

    say = MagicMock()
    clear = MagicMock(return_value=None)
    monkeypatch.setattr(standup, "say", say)
    monkeypatch.setattr(standup, "pop_user_updates", clear)

    r = await app.post(
        "/standup",
        data={"token": token, "user_name": "test-user", "text": "clear"},
        headers={"Content-type": "application/x-www-form-urlencoded"},
    )
    assert r.ok
    assert r.text == "No updates to clear!"
    assert clear.call_args[0] == ("test-user",)


async def test_standup_show_displays_current_status(app, monkeypatch, token):

    say = MagicMock()
    latest = MagicMock(return_value={"test-user": "debugging"})
    monkeypatch.setattr(standup, "say", say)
    monkeypatch.setattr(standup, "get_latest_updates", latest)

    standup.UPDATES = {"test-user": "debugging"}
    r = await app.post(
        "/standup",
        data={"token": token, "user_name": "test-user", "text": "show"},
        headers={"Content-type": "application/x-www-form-urlencoded"},
    )
    assert r.ok
    assert r.text == "debugging"


async def test_standup_show_is_empty(app, monkeypatch, token):

    say = MagicMock()
    monkeypatch.setattr(standup, "say", say)
    latest = MagicMock(return_value=dict())
    monkeypatch.setattr(standup, "get_latest_updates", latest)

    r = await app.post(
        "/standup",
        data={"token": token, "user_name": "test-user", "text": "show"},
        headers={"Content-type": "application/x-www-form-urlencoded"},
    )
    assert r.ok
    assert r.text == "I haven't received any updates from you yet, test-user."
