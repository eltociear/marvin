from marvin.responses import AtMentions


def test_at_mentions_believes(slack):
    atmentions = AtMentions(slack)
    msg = {'text': '<@UBEEMJZFX>', 'channel': 'foo'}
    atmentions([msg])
    assert slack.api_called_with('chat.postMessage', channel='foo')
