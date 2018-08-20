import pytest
from unittest.mock import MagicMock
import marvin


def test_at_mentions_responds_privately(app, token, monkeypatch):
    post_event = {"text": "<@UBEEMJZFX>", "channel": "foo", "type": "message.im"}
    say = MagicMock()
    monkeypatch.setattr(marvin.responses, "say", say)
    r = app.post("/", json={"event": post_event, "token": token})
    assert r.ok
    assert say.call_count == 1
    assert say.call_args[1]["channel"] == "foo"


def test_at_mentions_responds_publicly(app, token, monkeypatch):
    post_event = {
        "text": "technically irrelevant if the event is tagged",
        "channel": "foo",
        "type": "app_mention",
    }
    say = MagicMock()
    monkeypatch.setattr(marvin.responses, "say", say)
    r = app.post("/", json={"event": post_event, "token": token})
    assert r.ok
    assert say.call_count == 1
    assert say.call_args[1]["channel"] == "foo"


def test_at_mentions_doesnt_respond(app, token, monkeypatch):
    post_event = {"text": "<@UBEE>", "channel": "foo", "type": "message.im"}
    say = MagicMock()
    monkeypatch.setattr(marvin.responses, "say", say)
    r = app.post("/", json={"event": post_event, "token": token})
    assert r.ok
    assert say.call_count == 0


@pytest.mark.parametrize("event_type", ["app_mention", "message", "message.im"])
def test_at_mentions_doesnt_respond_if_marvin_tags_himself(
    app, token, monkeypatch, event_type
):
    post_event = {
        "text": "<@UBEEMJZFX>",
        "user": "UBEEMJZFX",
        "channel": "foo",
        "type": event_type,
    }
    say = MagicMock()
    monkeypatch.setattr(marvin.responses, "say", say)
    r = app.post("/", json={"event": post_event, "token": token})
    assert r.ok
    assert say.call_count == 0


def test_at_mentions_responds_within_thread(app, token, monkeypatch):
    post_event = {
        "text": "<@UBEEMJZFX>",
        "channel": "foo",
        "type": "message.im",
        "thread_ts": "00834934.0704",
    }
    say = MagicMock()
    monkeypatch.setattr(marvin.responses, "say", say)
    r = app.post("/", json={"event": post_event, "token": token})
    assert r.ok
    assert say.call_count == 1
    assert say.call_args[1]["channel"] == "foo"
    assert say.call_args[1]["thread_ts"] == "00834934.0704"


def test_slash_version_responds(app, token):
    r = app.post("/version", json={"channel": "foo", "token": token})
    assert r.ok
    assert "https://github.com" in r.text


def test_github_mentions_works(app, token, monkeypatch):
    post_event = {
        "text": "",
        "bot_id": "BBGMPFDHQ",
        "channel": "foo",
        "type": "message",
        "attachments": [
            {"text": "hey @cicdw you need to fix marvin", "title_link": "foo://bar"}
        ],
    }
    say = MagicMock()
    monkeypatch.setattr(
        marvin.responses, "get_dm_channel_id", lambda *args, **kwargs: "dm_chris"
    )
    monkeypatch.setattr(marvin.responses, "say", say)
    r = app.post("/", json={"event": post_event, "token": token})
    assert r.ok
    assert say.call_count == 1
    assert say.call_args[0] == ("You were mentioned on GitHub @ foo://bar",)
    assert say.call_args[1]["channel"] == "dm_chris"


def test_github_mentions_ignores_non_github_posts(app, token, monkeypatch):
    post_event = {
        "text": "",
        "channel": "foo",
        "type": "message",
        "attachments": [
            {"text": "hey @cicdw you need to fix marvin", "title_link": "foo://bar"}
        ],
    }
    say = MagicMock()
    monkeypatch.setattr(
        marvin.responses, "get_dm_channel_id", lambda *args, **kwargs: "dm_chris"
    )
    monkeypatch.setattr(marvin.responses, "say", say)
    r = app.post("/", json={"event": post_event, "token": token})
    assert r.ok
    assert say.call_count == 0


def test_github_mentions_tells_everyone(app, token, monkeypatch):
    post_event = {
        "text": "",
        "bot_id": "BBGMPFDHQ",
        "channel": "foo",
        "type": "message",
        "attachments": [
            {
                "text": "hey @cicdw @jlowin @joshmeek you need to fix marvin",
                "title_link": "foo://bar",
            }
        ],
    }
    say = MagicMock()
    monkeypatch.setattr(
        marvin.responses, "get_dm_channel_id", lambda *args, **kwargs: "dm_id"
    )
    monkeypatch.setattr(marvin.responses, "say", say)
    r = app.post("/", json={"event": post_event, "token": token})
    assert r.ok
    assert say.call_count == 3
