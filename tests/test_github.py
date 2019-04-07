import json
import hmac
import pytest

from apistar.http import Response
from unittest.mock import MagicMock

import marvin.github


@pytest.fixture
def create_header(secret):
    def _create_header(payload):
        encrypted = hmac.new(secret, msg=payload, digestmod="sha1").hexdigest()
        headers = {"x-hub-signature": f"sha1={encrypted}"}
        return headers

    return _create_header


def test_github_creates_issue_when_pr_is_merged(app, create_header, monkeypatch):
    data = {
        "pull_request": {
            "labels": [{"name": "core", "id": 1163480691}],
            "merged": True,
            "html_url": "foo:bar",
        },
        "action": "closed",
    }
    dumped = json.dumps(data).encode()
    create_issue = MagicMock(return_value=Response(""))
    monkeypatch.setattr(marvin.github, "create_issue", create_issue)
    r = app.post("/github/cloud", data=dumped, headers=create_header(dumped))
    assert r.ok
    assert create_issue.called
    assert create_issue.call_args[1]["title"] == "Cloud PR references Core"
    assert create_issue.call_args[1]["body"] == "See foo:bar for more details"
    assert create_issue.call_args[1]["labels"] == ["cloud-integration-notification"]


def test_github_doesnt_create_issue_when_pr_is_not_merged(
    app, create_header, monkeypatch
):
    data = {
        "pull_request": {
            "labels": [{"name": "core", "id": 1163480691}],
            "merged": False,
            "html_url": "foo:bar",
        },
        "action": "closed",
    }
    dumped = json.dumps(data).encode()
    create_issue = MagicMock(return_value=Response(""))
    monkeypatch.setattr(marvin.github, "create_issue", create_issue)
    r = app.post("/github/cloud", data=dumped, headers=create_header(dumped))
    assert r.ok
    assert not create_issue.called


def test_github_doesnt_create_issue_when_pr_is_not_labeled(
    app, create_header, monkeypatch
):
    data = {
        "pull_request": {
            "labels": [{"name": "cleanup", "id": 73}],
            "merged": True,
            "html_url": "foo:bar",
        },
        "action": "closed",
    }
    dumped = json.dumps(data).encode()
    create_issue = MagicMock(return_value=Response(""))
    monkeypatch.setattr(marvin.github, "create_issue", create_issue)
    r = app.post("/github/cloud", data=dumped, headers=create_header(dumped))
    assert r.ok
    assert not create_issue.called


def test_github_doesnt_create_issue_when_pr_is_not_closed(
    app, create_header, monkeypatch
):
    data = {
        "pull_request": {
            "labels": [{"name": "core", "id": 1163480691}],
            "merged": True,
            "html_url": "foo:bar",
        },
        "action": "reopened",
    }
    dumped = json.dumps(data).encode()
    create_issue = MagicMock(return_value=Response(""))
    monkeypatch.setattr(marvin.github, "create_issue", create_issue)
    r = app.post("/github/cloud", data=dumped, headers=create_header(dumped))
    assert r.ok
    assert not create_issue.called


@pytest.mark.parametrize("assoc", ["FIRST_TIME_CONTRIBUTOR", "NONE"])
def test_github_welcomes_new_contributors(app, assoc, create_header, monkeypatch):
    data = {
        "pull_request": {
            "author_association": assoc,
            "number": 42,
            "user": dict(login="marvin-robot"),
        },
        "action": "review_requested",
    }
    dumped = json.dumps(data).encode()
    make_pr_comment = MagicMock(return_value=Response(""))
    notify_chris = MagicMock()

    monkeypatch.setattr(marvin.github, "make_pr_comment", make_pr_comment)
    monkeypatch.setattr(marvin.github, "notify_chris", notify_chris)

    r = app.post("/github/core", data=dumped, headers=create_header(dumped))
    assert r.ok

    number, body = make_pr_comment.call_args[0]
    assert number == 42
    assert "@marvin-robot" in body
    assert "welcome" in body.lower()

    assert notify_chris.called
    assert notify_chris.call_args[0][0] == 42


def test_github_welcomes_new_contributors_only_once(app, create_header, monkeypatch):
    data = {
        "pull_request": {
            "author_association": "NONE",
            "number": 42,
            "user": dict(login="marvin-robot"),
        },
        "action": "review_requested",
    }
    dumped = json.dumps(data).encode()
    post = MagicMock(return_value=MagicMock(status_code=201))
    get_users = MagicMock(return_value={"chris": "chris"})
    get_dm_channel_id = MagicMock(return_value="X")
    say = MagicMock()

    # gotta patch everything so `notify_chris` successfully runs, else
    # it won't be cached
    monkeypatch.undo()
    monkeypatch.setattr(marvin.github.requests, "post", post)
    monkeypatch.setattr(marvin.github, "get_users", get_users)
    monkeypatch.setattr(marvin.github, "get_dm_channel_id", get_dm_channel_id)
    monkeypatch.setattr(marvin.github, "say", say)

    for _ in range(5):
        r = app.post("/github/core", data=dumped, headers=create_header(dumped))
        assert r.ok

    assert len([p for p in post.call_args_list if "42" in p[0][0]]) == 1
    assert say.call_count == 1


def test_github_doesnt_welcome_old_contributors(app, create_header, monkeypatch):
    data = {
        "pull_request": {
            "author_association": "CONTRIBUTOR",
            "number": 42,
            "user": dict(login="marvin-robot"),
        },
        "action": "review_requested",
    }
    dumped = json.dumps(data).encode()
    make_pr_comment = MagicMock(return_value=Response(""))
    monkeypatch.setattr(marvin.github, "make_pr_comment", make_pr_comment)
    r = app.post("/github/core", data=dumped, headers=create_header(dumped))
    assert r.ok
    assert not make_pr_comment.called


@pytest.mark.parametrize("action", ["reopened", "closed", "edited"])
def test_github_doesnt_welcome_new_contributors_on_other_actions(
    action, app, create_header, monkeypatch
):
    data = {
        "pull_request": {
            "author_association": "FIRST_TIME_CONTRIBUTOR",
            "number": 42,
            "user": dict(login="marvin-robot"),
        },
        "action": action,
    }
    dumped = json.dumps(data).encode()
    make_pr_comment = MagicMock(return_value=Response(""))
    monkeypatch.setattr(marvin.github, "make_pr_comment", make_pr_comment)
    r = app.post("/github/core", data=dumped, headers=create_header(dumped))
    assert r.ok
    assert not make_pr_comment.called
