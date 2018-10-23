import asyncio
import json
import operator
import re
from apistar.http import RequestData

from .utilities import get_pins, add_pin, remove_pin, say


MARVIN_ID = "UBEEMJZFX"
defcon_channel = "CDCN7CZDX"  # "CBH18KG8G" # engineering
levels = {
    1: ":matrixparrot:" * 7
    + "\n"
    + ":matrixparrot:  *DONT PANIC*  :matrixparrot:"
    + "\n"
    + ":matrixparrot:" * 7,
    2: "_Funny, how just when you think life can’t possibly get any worse it suddenly does._",
}


def level_updater(old_level, old_pin, extreme_level, extreme_msg, oper):
    if old_level == extreme_level:
        return extreme_msg
    elif old_level is None:
        return "DEFCON level has not been set yet!"

    new_level = oper(old_level, 1)
    text = levels.get(new_level, "")

    remove_pin(channel=defcon_channel, timestamp=old_pin["message"]["ts"])
    resp = say(f"*DEFCON LEVEL*: {new_level}\n" + text, channel=defcon_channel)
    data = json.loads(resp.text)
    add_pin(channel=defcon_channel, timestamp=data.get("ts", data.get("timestamp")))


async def defcon_handler(data: RequestData):
    payload = data.to_dict() if not isinstance(data, dict) else data
    update = payload.get("text")

    pins = get_pins(channel=defcon_channel)
    defcon_pins = [
        pin
        for pin in pins
        if pin["type"] == "message" and pin["message"]["user"] == MARVIN_ID
    ]
    if len(defcon_pins) <= 1:
        return "Multiple DEFCON pins found"

    defcon_pin = defcon_pins[0] if defcon_pins else None
    try:
        old_level = int(re.compile("\d").findall(defcon_pin["message"]["text"])[0])
    except:
        old_level = None

    lower_match = re.compile("^lower($|\s)")
    raise_match = re.compile("^raise($|\s)")
    level_match = re.compile("^\d($|\s)")

    ## logic for setting the level from scratch
    if level_match.match(update):
        new_level = int(level_match.match(update).string.strip())
        msg = levels.get(new_level, "")
        if defcon_pin:
            remove_pin(channel=defcon_channel, timestamp=defcon_pin["message"]["ts"])
        resp = say(f"*DEFCON LEVEL*: {new_level}" + msg, channel=defcon_channel)
        data = json.loads(resp.text)
        add_pin(channel=defcon_channel, timestamp=data.get("ts", data.get("timestamp")))
        return ""

    if lower_match.match(update.lower()):
        level_updater(
            old_level,
            defcon_pin,
            1,
            "DEFCON level is already as low as it can be!",
            operator.sub,
        )
        return ""

    if raise_match.match(update.lower()):
        level_updater(
            old_level,
            defcon_pin,
            5,
            "DEFCON level is already as high as it can be!",
            operator.add,
        )
        return ""
