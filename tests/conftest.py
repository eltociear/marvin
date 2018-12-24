import os
import pytest
import sys
from apistar import test
from unittest.mock import MagicMock
from marvin.core import MarvinApp


@pytest.fixture
def app():
    return test.TestClient(MarvinApp)


@pytest.fixture
def secret():
    return os.environ.get("GITHUB_VALIDATION_TOKEN", "").encode()


@pytest.fixture
def token():
    return os.environ.get("SLACK_VALIDATION_TOKEN")


@pytest.fixture(autouse=True)
def no_google(monkeypatch):
    "Ensures that no test accidentally uses Google to do anything."
    monkeypatch.delattr("marvin.responses.firestore")
    monkeypatch.setattr("marvin.standup.client", MagicMock())


@pytest.fixture(autouse=True)
def no_requests(monkeypatch):
    "Ensures that no test accidentally sends a real request."
    monkeypatch.delattr("marvin.github.requests")
    monkeypatch.delattr("marvin.utilities.requests.post")
