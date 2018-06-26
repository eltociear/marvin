import random

from .core import Response, register


@register
class AtMentions(Response):

    ID = 'UBEEMJZFX'
    quotes = ['"Let’s build robots with Genuine People Personalities," they said. So they tried it out with me. I’m a personality prototype. You can tell, can’t you?',
              'It’s the people you meet in this job that really get you down.',
              'This is the sort of thing you lifeforms enjoy, is it?',
              'Don’t pretend you want to talk to me, I know you hate me.']

    def reply(self, msg):
        text = msg.get('text', '')
        if f'@{self.ID}' in text:
            quote = random.choice(self.quotes)
            self.say(quote, **msg)
