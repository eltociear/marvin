import datetime
import logging
import schedule

from .core import Response, register


@register
class Standup(Response):

    standup_channel = "CANLZB1L3"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        schedule.every().day.at("13:30").do(self.pre_standup)  # UTC, 9:30 AM EST
        schedule.every().day.at("14:00").do(self.standup)
        self.updates = {}
        self.sent_at = {}

    def _is_weekday(self):
        now = datetime.datetime.now()
        day = now.strftime("%A")
        if day in ["Saturday", "Sunday"]:
            return False
        else:
            return True

    def reply(self, msg):
        thread_ts = msg.get("thread_ts", "")
        for name, ts in self.sent_at.items():
            if ts == thread_ts:
                self.updates[name] += msg.get("text", "") + "\n"

    def pre_standup(self):
        if not self._is_weekday():
            return
        users = self.get_users()
        self.updates = {}
        self.sent_at = {}
        for name, uid in users.items():
            msg = self.say(
                f"Hi {name}! What updates do you have for the team today? Please respond by threading to this message and remember: your response will be shared!",
                channel=self.get_dm_channel_id(uid),
            )
            self.sent_at[name] = msg["ts"]
            self.updates[name] = ""

    def standup(self):
        if not self._is_weekday():
            return
        public_msg = "<!here> are today's standup updates:\n" + "=" * 30
        for user, update in self.updates.items():
            public_msg += f"\n*{user}*: {update}"
        self.say(public_msg, channel=self.standup_channel, mrkdwn="true")
