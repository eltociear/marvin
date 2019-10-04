import inspect
import os
import sys
from unittest.mock import MagicMock

import pytest
from requests_async import ASGISession

from marvin.core import MarvinApp


def pytest_collection_modifyitems(session, config, items):
    """
    Modify tests prior to execution
    """
    for item in items:
        # automatically add @pytest.mark.asyncio to async tests
        if isinstance(item, pytest.Function) and inspect.iscoroutinefunction(
            item.function
        ):
            item.add_marker(pytest.mark.asyncio)


@pytest.fixture
async def app():
    yield ASGISession(MarvinApp)


@pytest.fixture
def secret():
    return os.environ.get("GITHUB_VALIDATION_TOKEN", "").encode()


@pytest.fixture
def token():
    return os.environ.get("SLACK_VALIDATION_TOKEN")


@pytest.fixture(autouse=True)
def no_google(monkeypatch):
    "Ensures that no test accidentally uses Google to do anything."
    monkeypatch.delattr("marvin.firestore.client")
    monkeypatch.setattr("marvin.standup.client", MagicMock())


@pytest.fixture(autouse=True)
def no_requests(monkeypatch):
    "Ensures that no test accidentally sends a real request."
    monkeypatch.delattr("marvin.github.requests")
    monkeypatch.delattr("marvin.utilities.requests.post")
