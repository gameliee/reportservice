import pytest
from fastapi.testclient import TestClient
from pymongo import MongoClient
from reportservice.app import app
from .settings import settings


@pytest.fixture(scope="session")
def monkeypatch_session():
    from _pytest.monkeypatch import MonkeyPatch

    m = MonkeyPatch()
    yield m
    m.undo()


@pytest.fixture(scope="session", autouse=True)
def patch_settings(monkeypatch_session, temp_log_file, dburi, random_database_name):
    monkeypatch_session.setattr(settings, "DB_URL", dburi)
    monkeypatch_session.setattr(settings, "LOG_FILE", temp_log_file)
    monkeypatch_session.setattr(settings, "DB_REPORT_NAME", random_database_name)


@pytest.fixture(scope="session", autouse=True)
def delete_random_collection(patch_settings, dburi, random_database_name):
    yield None
    # mongo = MongoClient(dburi)
    # mongo.drop_database(random_database_name)


@pytest.fixture(scope="session", autouse=True)
def testsettings(monkeypatch_session, dburi):
    return settings


@pytest.fixture(scope="session")
def testclient(dburi):
    with TestClient(app) as client:
        yield client
