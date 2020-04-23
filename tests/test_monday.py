import marvin
from unittest.mock import MagicMock

async def test_slash_monday_responds(app, token, monkeypatch):
    monkeypatch.setattr(marvin.monday.requests.post, MagicMock())
    r = await app.post("/monday", json={"channel": "foo", "username": "bar", "text": "some text", "token": token})
    assert r.ok
    assert "item created..." in r.text