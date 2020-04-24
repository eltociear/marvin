import marvin
from unittest.mock import MagicMock


async def test_slash_monday_responds(app, token, monkeypatch):
    monkeypatch.setattr("marvin.monday.requests", MagicMock())
    r = await app.post(
        "/monday",
        json={"channel": "foo", "username": "bar", "text": "some text", "token": token},
    )
    assert r.ok
    assert (
        "It gives me a headache just trying to think down to your level, but I have added this to Monday."
        in r.text
    )
