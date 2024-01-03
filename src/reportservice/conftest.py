import uuid
import pytest
from fastapi.testclient import TestClient
from reportservice.app import app
from .settings import settings


@pytest.fixture(scope="session")
def monkeypatch_session():
    from _pytest.monkeypatch import MonkeyPatch

    m = MonkeyPatch()
    yield m
    m.undo()


@pytest.fixture(scope="session", autouse=True)
def patch_settings(monkeypatch_session, temp_log_file):
    monkeypatch_session.setattr(settings, "LOG_FILE", temp_log_file)


@pytest.fixture(scope="session")
def testclient():
    with TestClient(app) as cl:
        yield cl
