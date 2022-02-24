import json
import pytest
from collections import namedtuple
from unittest.mock import MagicMock
import marvin
from marvin.utilities import (
    cache_with_key,
    get_channels,
    get_users,
    get_dm_channel_id,
    say,
)


@pytest.fixture
def postdata():
    return namedtuple("ReturnPost", ["ok", "text"])


def test_get_channels_returns_user_dict(monkeypatch, postdata):
    returned = dict(channels=[dict(name="channel5news", id="1")])
    post = MagicMock(return_value=postdata(ok=True, text=json.dumps(returned)))
    monkeypatch.setattr(marvin.utilities.requests, "post", post, raising=False)
    channels = get_channels()
    assert len(channels) == 1
    assert channels["channel5news"] == "1"


def test_get_channels_returns_empty_dict_if_request_fails(monkeypatch, postdata):
    returned = dict(channels=[dict(name="channel5news", id="1")])
    post = MagicMock(return_value=postdata(ok=False, text=json.dumps(returned)))
    monkeypatch.setattr(marvin.utilities.requests, "post", post, raising=False)
    channels = get_channels()
    assert isinstance(channels, dict)
    assert len(channels) == 0


def test_get_users_returns_user_dict(monkeypatch, postdata):
    returned = dict(members=[dict(is_bot=False, name="chris", id="1")])
    post = MagicMock(return_value=postdata(ok=True, text=json.dumps(returned)))
    monkeypatch.setattr(marvin.utilities.requests, "post", post, raising=False)
    users = get_users()
    assert len(users) == 1
    assert users["chris"] == "1"


def test_get_users_returns_empty_dict_if_request_fails(monkeypatch, postdata):
    returned = dict(members=[dict(is_bot=False, name="chris", id="1")])
    post = MagicMock(return_value=postdata(ok=False, text=json.dumps(returned)))
    monkeypatch.setattr(marvin.utilities.requests, "post", post, raising=False)
    users = get_users()
    assert isinstance(users, dict)
    assert len(users) == 0


def test_get_users_ignores_slackbot_and_other_bots(monkeypatch, postdata):
    returned = dict(
        members=[
            dict(is_bot=False, name="chris", id="1"),
            dict(is_bot=True, name="jeremiah", id=2),
            dict(is_bot=False, name="slackbot", id=3),
            dict(is_bot=False, name="test-user", id=4),
        ]
    )
    post = MagicMock(return_value=postdata(ok=True, text=json.dumps(returned)))
    monkeypatch.setattr(marvin.utilities.requests, "post", post, raising=False)
    users = get_users()
    assert len(users) == 1
    assert users["chris"] == "1"


def test_get_dm_channel_returns_id(monkeypatch, postdata):
    returned = dict(channel=dict(id=94611, noise="xx"))
    post = MagicMock(return_value=postdata(ok=True, text=json.dumps(returned)))
    monkeypatch.setattr(marvin.utilities.requests, "post", post, raising=False)
    channel_id = get_dm_channel_id("irrelevant_string")
    assert channel_id == 94611


def test_get_dm_channel_returns_none_on_failed_request(monkeypatch, postdata):
    returned = dict(channel=dict(id=94611, noise="xx"))
    post = MagicMock(return_value=postdata(ok=False, text=json.dumps(returned)))
    monkeypatch.setattr(marvin.utilities.requests, "post", post, raising=False)
    channel_id = get_dm_channel_id("irrelevant_string")
    assert channel_id is None


def test_cache_with_key_caches():
    @cache_with_key
    def random_func():
        import random

        return round(random.random(), 6)

    x = random_func("x")
    y = random_func("y")

    assert isinstance(x, float)
    assert isinstance(y, float)

    assert x != y
    assert x == random_func("x")
    assert y == random_func("y")
