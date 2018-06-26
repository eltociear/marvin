import logging
import re
import sys


class Post(object):

    @property
    def name(self):
        return type(self).__name__

    def say(self, words, channel=None, **kwargs):
        self.log.info('{0} saying "{1}" in channel {2}'.format(self.name, words, channel))
        posted_msg = self.slack_client.api_call("chat.postMessage",
                                    channel=channel,
                                    text=words,
                                    as_user=True)
        return posted_msg

    def react(self, emoji, channel=None, ts=None, **kwargs):
        txt = kwargs.get('text')
        self.log.info('{0} reacting to "{1}" with :{2}: in channel {3}'.format(self.name, txt, emoji, channel))
        posted_msg = self.slack_client.api_call("reactions.add",
                                    channel=channel,
                                    name=emoji,
                                    timestamp=ts, as_user=True)
        return posted_msg

    def __init__(self, slack_client):
        self.slack_client = slack_client
        self.log = logging.getLogger(self.name)
