import asyncio
import datetime
import pytest
from unittest.mock import MagicMock
from marvin import defcon


@pytest.mark.parametrize("text", ["5", "raise", "lower"])
def test_defcon_can_be_updated(app, monkeypatch, token, text):
    say = MagicMock(return_value=MagicMock(text='{"ts": "yesterday"}'))
    monkeypatch.setattr(defcon, "say", say)
    monkeypatch.setattr(defcon, "add_pin", say)
    monkeypatch.setattr(defcon, "get_pins", say)

    r = app.post(
        "/defcon", json={"token": token, "user_name": "test-user", "text": text}
    )
    assert r.ok
    assert r.text == ""


@pytest.mark.parametrize("text", ["5", "raise", "lower"])
def test_defcon_complains_if_too_many_pins_found(app, monkeypatch, token, text):
    pins = [
        {"type": "message", "message": {"user": defcon.MARVIN_ID}},
        {"type": "message", "message": {"user": defcon.MARVIN_ID}},
    ]
    monkeypatch.setattr(defcon, "get_pins", MagicMock(return_value=pins))

    r = app.post(
        "/defcon", json={"token": token, "user_name": "test-user", "text": text}
    )
    assert r.ok
    assert "Multiple DEFCON pins" in r.text
