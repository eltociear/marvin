import os
import pytest
from apistar import test
from unittest.mock import MagicMock
from marvin.core import MarvinApp


@pytest.fixture
def app():
    return test.TestClient(MarvinApp)


@pytest.fixture
def token():
    return os.environ.get("SLACK_VALIDATION_TOKEN")


@pytest.fixture(autouse=True)
def no_requests(monkeypatch):
    "Ensures that no test accidentally sends a real request."
    monkeypatch.delattr("marvin.utilities.requests.post")
