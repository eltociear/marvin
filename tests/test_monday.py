import marvin
from unittest.mock import MagicMock


async def test_slash_monday_roadmap_responds(app, token, monkeypatch):
    monkeypatch.setattr("marvin.monday.requests", MagicMock())
    monkeypatch.setattr(marvin.utilities.requests, "post", MagicMock(), raising=False)
    r = await app.post(
        "/monday-roadmap",
        data={
            "channel_name": "foo",
            "user_name": "bar",
            "text": "some text",
            "token": token,
        },
    )
    assert r.ok
    assert (
        "It gives me a headache just trying to think down to your level, but I have added this to Monday."
        in r.text
    )


async def test_slash_monday_blogs_responds(app, token, monkeypatch):
    monkeypatch.setattr("marvin.monday.requests", MagicMock())
    monkeypatch.setattr(marvin.utilities.requests, "post", MagicMock(), raising=False)
    r = await app.post(
        "/monday-blogs",
        data={
            "channel_name": "foo",
            "user_name": "bar",
            "text": "some text",
            "token": token,
        },
    )
    assert r.ok
    assert (
        "It gives me a headache just trying to think down to your level, but I have added this to Monday."
        in r.text
    )


async def test_slash_monday_customer_feedback_responds(app, token, monkeypatch):
    monkeypatch.setattr("marvin.monday.requests", MagicMock())
    monkeypatch.setattr(marvin.utilities.requests, "post", MagicMock(), raising=False)
    r = await app.post(
        "/monday-customer-feedback",
        data={
            "channel_name": "foo",
            "user_name": "bar",
            "text": "some text",
            "token": token,
        },
    )
    assert r.ok
    assert (
        "It gives me a headache just trying to think down to your level, but I have added this to Monday."
        in r.text
    )


async def test_slash_monday_any_board_responds(app, token, monkeypatch):
    monkeypatch.setattr("marvin.monday.requests", MagicMock())
    monkeypatch.setattr(marvin.utilities.requests, "post", MagicMock(), raising=False)
    r = await app.post(
        "/monday-any-board",
        data={
            "channel_name": "foo",
            "user_name": "bar",
            "text": "585522431 some text",
            "token": token,
        },
    )
    assert r.ok
    assert (
        "It gives me a headache just trying to think down to your level, but I have added this to Monday."
        in r.text
    )


async def test_slash_monday_any_board_responds_invalid_board_id(
    app, token, monkeypatch
):
    monkeypatch.setattr("marvin.monday.requests", MagicMock())
    monkeypatch.setattr(marvin.utilities.requests, "post", MagicMock(), raising=False)
    r = await app.post(
        "/monday-any-board",
        data={
            "channel_name": "foo",
            "user_name": "bar",
            "text": "some text",
            "token": token,
        },
    )
    assert r.ok
    assert (
        "A valid board id has not been provided. Try again with the board id followed by a space."
        in r.text
    )
