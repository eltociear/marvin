import json
import pytest
from collections import namedtuple
from unittest.mock import MagicMock
import marvin
from marvin.utilities import get_users, get_dm_channel_id, say


@pytest.fixture
def postdata():
    return namedtuple('ReturnPost', ['ok', 'text'])


def test_get_users_returns_user_dict(monkeypatch, postdata):
    returned = dict(members=[dict(is_bot=False,
                                  name='chris',
                                  id='1')])
    post = MagicMock(return_value=postdata(ok=True,
                                           text=json.dumps(returned)))
    monkeypatch.setattr(marvin.utilities.requests, "post", post, raising=False)
    users = get_users()
    assert len(users) == 1
    assert users['chris'] == '1'
