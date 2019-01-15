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
