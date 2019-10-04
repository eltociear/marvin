from unittest.mock import MagicMock

import pytest

import marvin.responses
import marvin.users


@pytest.fixture(autouse=True, scope="module")
def set_users():
    marvin.users.USERS.update(
        {
            "q6kqpHrZcLLekeToWvrB": {
                "name": "Chris",
                "email": "chris@prefect.io",
                "slack": "UBBE1SC8L",
                "notion": "Chris",
                "github": "cicdw",
            },
            "rvFokTPSoHca1pyGJpL8": {
                "email": "josh@prefect.io",
                "slack": "UBE4N2LG1",
                "notion": "Josh",
                "github": "joshmeek",
                "name": "Josh",
            },
            "IVHJCBIxbLHA3iQniVUQ": {
                "name": "Jeremiah",
                "email": "jeremiah@prefect.io",
                "slack": "UAPLR5SHL",
                "github": "jlowin",
                "notion": "Jeremiah",
            },
        }
    )


async def test_at_mentions_responds_privately(app, token, monkeypatch):
    post_event = {"text": "<@UBEEMJZFX>", "channel": "foo", "type": "message.im"}
    say = MagicMock()
    monkeypatch.setattr(marvin.responses, "say", say)
    r = await app.post("/", json={"event": post_event, "token": token})
    assert r.ok
    assert say.call_count == 1
    assert say.call_args[1]["channel"] == "foo"


async def test_at_mentions_responds_publicly(app, token, monkeypatch):
    post_event = {
        "text": "technically irrelevant if the event is tagged",
        "channel": "foo",
        "type": "app_mention",
    }
    say = MagicMock()
    monkeypatch.setattr(marvin.responses, "say", say)
    r = await app.post("/", json={"event": post_event, "token": token})
    assert r.ok
    assert say.call_count == 1
    assert say.call_args[1]["channel"] == "foo"


async def test_at_mentions_doesnt_respond(app, token, monkeypatch):
    post_event = {"text": "<@UBEE>", "channel": "foo", "type": "message.im"}
    say = MagicMock()
    monkeypatch.setattr(marvin.responses, "say", say)
    r = await app.post("/", json={"event": post_event, "token": token})
    assert r.ok
    assert say.call_count == 0


@pytest.mark.parametrize("event_type", ["app_mention", "message", "message.im"])
async def test_at_mentions_doesnt_respond_if_marvin_tags_himself(
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
    r = await app.post("/", json={"event": post_event, "token": token})
    assert r.ok
    assert say.call_count == 0


async def test_marvin_gives_psa_when_new_emoji_added(app, token, monkeypatch):
    post_event = {"type": "emoji_changed", "subtype": "add", "name": "test-emoji"}
    say = MagicMock()
    monkeypatch.setattr(marvin.responses, "say", say)
    r = await app.post("/", json={"event": post_event, "token": token})
    assert r.ok
    assert say.call_count == 1
    assert (
        say.call_args[0][0]
        == "*PSA*: A new slackmoji :test-emoji: was added! :more_you_know:"
    )
    assert say.call_args[1]["channel"] == "CANPVTSKU"


async def test_marvin_only_gives_psa_for_additions(app, token, monkeypatch):
    post_event = {"type": "emoji_changed", "subtype": "changed", "name": "test-emoji"}
    say = MagicMock()
    monkeypatch.setattr(marvin.responses, "say", say)
    r = await app.post("/", json={"event": post_event, "token": token})
    assert r.ok
    assert say.call_count == 0


async def test_at_mentions_responds_within_thread(app, token, monkeypatch):
    post_event = {
        "text": "<@UBEEMJZFX>",
        "channel": "foo",
        "type": "message.im",
        "thread_ts": "00834934.0704",
    }
    say = MagicMock()
    monkeypatch.setattr(marvin.responses, "say", say)
    r = await app.post("/", json={"event": post_event, "token": token})
    assert r.ok
    assert say.call_count == 1
    assert say.call_args[1]["channel"] == "foo"
    assert say.call_args[1]["thread_ts"] == "00834934.0704"


async def test_slash_version_responds(app, token):
    r = await app.post("/version", json={"channel": "foo", "token": token})
    assert r.ok
    assert "https://github.com" in r.text


async def test_github_mentions_works(app, token, monkeypatch):
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
    r = await app.post("/", json={"event": post_event, "token": token})
    assert r.ok
    assert say.call_count == 1
    assert say.call_args[0] == ("You were mentioned on GitHub @ foo://bar",)
    assert say.call_args[1]["channel"] == "dm_chris"


async def test_github_mentions_ignores_non_github_posts(app, token, monkeypatch):
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
    r = await app.post("/", json={"event": post_event, "token": token})
    assert r.ok
    assert say.call_count == 0


async def test_github_mentions_tells_everyone(app, token, monkeypatch):
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
    r = await app.post("/", json={"event": post_event, "token": token})
    assert r.ok
    assert say.call_count == 3


async def test_notion_mentions_works(app, token, monkeypatch):
    post_event = {
        "text": "Chris White commented in *<https://foo.bar/baz/page|This is not real ignore this>*",
        "bot_id": "BDUBG9WAD",
        "channel": "foo",
        "type": "message",
        "attachments": [{"text": "hey @Chris White you need to fix marvin"}],
    }
    say = MagicMock()
    monkeypatch.setattr(
        marvin.responses, "get_dm_channel_id", lambda *args, **kwargs: "dm_chris"
    )
    monkeypatch.setattr(marvin.responses, "say", say)
    r = await app.post("/", json={"event": post_event, "token": token})
    assert r.ok
    assert say.call_count == 1
    assert say.call_args[0] == (
        "You were mentioned on Notion @ https://foo.bar/baz/page",
    )
    assert say.call_args[1]["channel"] == "dm_chris"


async def test_notion_mentions_works_with_multiple_attachments(app, token, monkeypatch):
    post_event = {
        "text": "Chris White commented in *<https://foo.bar/baz/page|This is not real ignore this>*",
        "bot_id": "BDUBG9WAD",
        "channel": "foo",
        "type": "message",
        "attachments": [
            {"text": "hey @Chris White you need to fix marvin"},
            {"text": "hey @Josh this is random"},
            {"text": "hey @Nobody this shouldn't notify at all"},
        ],
    }
    say = MagicMock()
    monkeypatch.setattr(
        marvin.responses, "get_dm_channel_id", lambda *args, **kwargs: "dm_chris"
    )
    monkeypatch.setattr(marvin.responses, "say", say)
    r = await app.post("/", json={"event": post_event, "token": token})
    assert r.ok
    assert say.call_count == 2
    assert say.call_args[0] == (
        "You were mentioned on Notion @ https://foo.bar/baz/page",
    )
    assert say.call_args[1]["channel"] == "dm_chris"


async def test_notion_mentions_tells_everyone(app, token, monkeypatch):
    post_event = {
        "text": "Billy Bob commented in *<https://foo.bar/baz/page|This is not real ignore this>*",
        "bot_id": "BDUBG9WAD",
        "channel": "foo",
        "type": "message",
        "attachments": [
            {
                "text": "hey @Chris White you need to fix marvin and @Josh Meek keep up the good work"
            }
        ],
    }
    say = MagicMock()
    monkeypatch.setattr(
        marvin.responses, "get_dm_channel_id", lambda *args, **kwargs: "dm_id"
    )
    monkeypatch.setattr(marvin.responses, "say", say)
    r = await app.post("/", json={"event": post_event, "token": token})
    assert r.ok
    assert say.call_count == 2
