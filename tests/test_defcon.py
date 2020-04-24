import asyncio
import datetime
from unittest.mock import MagicMock

import pytest

from marvin import defcon


@pytest.mark.parametrize("text", ["5", "raise", "lower"])
async def test_defcon_can_be_updated(app, monkeypatch, token, text):
    pins = [
        {
            "type": "message",
            "message": {
                "user": defcon.MARVIN_ID,
                "ts": "yesterday",
                "text": "DEFCON LEVEL: 3",
            },
        }
    ]
    monkeypatch.setattr(defcon, "get_pins", MagicMock(return_value=pins))
    say = MagicMock(return_value=MagicMock(text='{"ts": "yesterday"}'))
    add_pin, remove_pin = MagicMock(), MagicMock()
    monkeypatch.setattr(defcon, "say", say)
    monkeypatch.setattr(defcon, "add_pin", add_pin)
    monkeypatch.setattr(defcon, "remove_pin", remove_pin)
    monkeypatch.setattr(defcon, "get_pins", MagicMock(return_value=pins))

    r = await app.post(
        "/defcon",
        data={"token": token, "user_name": "test-user", "text": text},
        headers={"Content-type": "application/x-www-form-urlencoded"},
    )
    assert r.ok
    assert r.text == "DEFCON level updated!"
    assert add_pin.called_once
    assert remove_pin.called_once


@pytest.mark.parametrize("text", ["5", "4", "3", "2", "1", "raise", "lower"])
async def test_defcon_levels_format_correctly(app, monkeypatch, token, text):
    pins = [
        {
            "type": "message",
            "message": {
                "user": defcon.MARVIN_ID,
                "ts": "yesterday",
                "text": "DEFCON LEVEL: 3",
            },
        }
    ]
    monkeypatch.setattr(defcon, "get_pins", MagicMock(return_value=pins))
    say = MagicMock(return_value=MagicMock(text='{"ts": "yesterday"}'))
    add_pin, remove_pin = MagicMock(), MagicMock()
    monkeypatch.setattr(defcon, "say", say)
    monkeypatch.setattr(defcon, "add_pin", add_pin)
    monkeypatch.setattr(defcon, "remove_pin", remove_pin)
    monkeypatch.setattr(defcon, "get_pins", MagicMock(return_value=pins))

    r = await app.post(
        "/defcon",
        data={"token": token, "user_name": "test-user", "text": text},
        headers={"Content-type": "application/x-www-form-urlencoded"},
    )

    if text == "raise":
        level = 4
    elif text == "lower":
        level = 2
    else:
        level = int(text)

    assert say.call_args[0][0] == f"*DEFCON LEVEL*: {level}\n{defcon.levels[level]}"


@pytest.mark.parametrize("text", ["raise", "lower"])
async def test_defcon_informatively_complains_if_no_level_set(
    app, monkeypatch, token, text
):
    monkeypatch.setattr(defcon, "get_pins", MagicMock(return_value=[]))

    r = await app.post(
        "/defcon",
        data={"token": token, "user_name": "test-user", "text": text},
        headers={"Content-type": "application/x-www-form-urlencoded"},
    )
    assert r.ok
    assert (
        r.text == "DEFCON level has not been set yet! Use `/defcon NUMBER` to set one."
    )


@pytest.mark.parametrize("text", ["5", "raise", "lower"])
async def test_defcon_complains_if_too_many_pins_found(app, monkeypatch, token, text):
    pins = [
        {"type": "message", "message": {"user": defcon.MARVIN_ID}},
        {"type": "message", "message": {"user": defcon.MARVIN_ID}},
    ]
    monkeypatch.setattr(defcon, "get_pins", MagicMock(return_value=pins))

    r = await app.post(
        "/defcon",
        data={"token": token, "user_name": "test-user", "text": text},
        headers={"Content-type": "application/x-www-form-urlencoded"},
    )
    assert r.ok
    assert "Multiple DEFCON pins" in r.text
