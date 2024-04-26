import pytest
from fastapi.testclient import TestClient
from pymongo import MongoClient

from .settings import settings


@pytest.fixture(scope="session")
def monkeypatch_session():
    from _pytest.monkeypatch import MonkeyPatch

    m = MonkeyPatch()
    yield m
    m.undo()


@pytest.fixture(scope="session", autouse=True)
def patch_settings(monkeypatch_session, temp_log_file, random_database_name):
    monkeypatch_session.setattr(settings, "LOG_FILE", temp_log_file)
    monkeypatch_session.setattr(settings, "DB_REPORT_NAME", random_database_name)
    monkeypatch_session.setattr(settings, "PROFILING_ENABLED", True)
    assert settings.LOG_FILE == temp_log_file
    assert settings.DB_REPORT_NAME == random_database_name
    assert settings.PROFILING_ENABLED is True


@pytest.fixture(scope="session", autouse=True)
def delete_random_database(patch_settings, admindburi, random_database_name):
    yield None
    mongo = MongoClient(admindburi)
    mongo.drop_database(random_database_name)


@pytest.fixture(scope="session", autouse=True)
def testsettings(monkeypatch_session):
    return settings


@pytest.fixture(scope="session")
def testclient(patch_settings):
    from reportservice.app import app

    with TestClient(app) as client:
        yield client
