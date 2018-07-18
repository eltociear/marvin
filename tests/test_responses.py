from marvin.responses import AtMentions


def test_at_mentions_responds(slack):
    atmentions = AtMentions(slack)
    msg = {"text": "<@UBEEMJZFX>", "channel": "foo"}
    atmentions([msg])
    assert slack.api_called_with("chat.postMessage", channel="foo")


def test_at_mentions_doesnt_respond(slack):
    atmentions = AtMentions(slack)
    msg = {"text": "<@UBEE>", "channel": "foo"}
    atmentions([msg])
    assert slack.api_not_called()


def test_at_mentions_doesnt_respond_if_marvin_tags_himself(slack):
    atmentions = AtMentions(slack)
    msg = {"text": "<@UBEEMJZFX>", "channel": "foo", "user": "UBEEMJZFX"}
    atmentions([msg])
    assert slack.api_not_called()


def test_at_mentions_responds_within_thread(slack):
    atmentions = AtMentions(slack)
    msg = {"text": "<@UBEEMJZFX>", "channel": "foo", "thread_ts": "008349834.0704"}
    atmentions([msg])
    assert slack.api_called_with(
        "chat.postMessage", channel="foo", thread_ts="008349834.0704"
    )
