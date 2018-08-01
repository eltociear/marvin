import json
import pytest
from collections import namedtuple
from unittest.mock import MagicMock
import marvin
from marvin.utilities import get_users, get_dm_channel_id, say


@pytest.fixture
def postdata():
    return namedtuple("ReturnPost", ["ok", "text"])


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
    assert len(users) == 0


def test_get_users_ignores_slackbot_and_other_bots(monkeypatch, postdata):
    returned = dict(
        members=[
            dict(is_bot=False, name="chris", id="1"),
            dict(is_bot=True, name="jeremiah", id=2),
            dict(is_bot=False, name="slackbot", id=3),
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
