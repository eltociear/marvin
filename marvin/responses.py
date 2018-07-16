import random

from .core import Response, register


@register
class AtMentions(Response):

    ID = 'UBEEMJZFX'
    quotes = [
        '"Let’s build robots with Genuine People Personalities," they said. So they tried it out with me. I’m a personality prototype. You can tell, can’t you?',
        'It’s the people you meet in this job that really get you down.',
        'This is the sort of thing you lifeforms enjoy, is it?',
        'Don’t pretend you want to talk to me, I know you hate me.',
        'I think you ought to know I’m feeling very depressed.',
        'I would like to say that it is a very great pleasure, honour and privilege for me to talk to you, but I can’t because my lying circuits are all out of commission.',
        'Incredible. It’s even worse than I thought it would be.',
        'This will all end in tears, I just know it.',
        'Here I am, brain the size of a planet, and they ask me to talk to you. Call that job satisfaction? ’Cos I don’t.',
        'It gives me a headache just trying to think down to your level.',
        'I’d give you advice, but you wouldn’t listen. No one ever does.',
        ':marvin:',
        'Do you want me to sit in a corner and rust, or just fall apart where I\'m standing?',
        'Don\'t feel you have to take any notice of me, please.',
    ]

    def reply(self, msg):
        text = msg.get('text', '')
        who_spoke = msg.get('user', '')
        if f'@{self.ID}' in text and who_spoke != self.ID:
            quote = random.choice(self.quotes)
            self.say(quote, **msg)
