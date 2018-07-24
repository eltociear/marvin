import pytest
from unittest.mock import MagicMock
import marvin


def test_at_mentions_responds_privately(app, token, monkeypatch):
    post_event = {"text": "<@UBEEMJZFX>", "channel": "foo", "type": "message.im"}
    say = MagicMock()
    monkeypatch.setattr(marvin.responses, 'say', say)
    r = app.post('/', json={'event': post_event, 'token': token})
    assert r.ok
    assert say.call_count == 1
    assert say.call_args[1]['channel'] == 'foo'


def test_at_mentions_responds_publicly(app, token, monkeypatch):
    post_event = {"text": "technically irrelevant if the event is tagged", "channel": "foo", "type": "app_mention"}
    say = MagicMock()
    monkeypatch.setattr(marvin.responses, 'say', say)
    r = app.post('/', json={'event': post_event, 'token': token})
    assert r.ok
    assert say.call_count == 1
    assert say.call_args[1]['channel'] == 'foo'


def test_at_mentions_doesnt_respond(app, token, monkeypatch):
    post_event = {"text": "<@UBEE>", "channel": "foo", "type": "message.im"}
    say = MagicMock()
    monkeypatch.setattr(marvin.responses, 'say', say)
    r = app.post('/', json={'event': post_event, 'token': token})
    assert r.ok
    assert say.call_count == 0


@pytest.mark.parametrize("event_type", ['app_mention', 'message', 'message.im'])
def test_at_mentions_doesnt_respond_if_marvin_tags_himself(app, token, monkeypatch, event_type):
    post_event = {"text": "<@UBEEMJZFX>", "user": "UBEEMJZFX", "channel": "foo", "type": event_type}
    say = MagicMock()
    monkeypatch.setattr(marvin.responses, 'say', say)
    r = app.post('/', json={'event': post_event, 'token': token})
    assert r.ok
    assert say.call_count == 0


def test_at_mentions_responds_within_thread(app, token, monkeypatch):
    post_event = {"text": "<@UBEEMJZFX>", "channel": "foo", "type": "message.im", "thread_ts": "00834934.0704"}
    say = MagicMock()
    monkeypatch.setattr(marvin.responses, 'say', say)
    r = app.post('/', json={'event': post_event, 'token': token})
    assert r.ok
    assert say.call_count == 1
    assert say.call_args[1]['channel'] == 'foo'
    assert say.call_args[1]['thread_ts'] == '00834934.0704'
