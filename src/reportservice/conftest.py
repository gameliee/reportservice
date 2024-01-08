import uuid
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
def patch_settings(monkeypatch_session, temp_log_file, dburi, random_collection_name):
    monkeypatch_session.setattr(settings, "DB_URL", dburi)
    monkeypatch_session.setattr(settings, "LOG_FILE", temp_log_file)
    monkeypatch_session.setattr(settings, "DB_COLLECTION_SETTINGS", random_collection_name)


@pytest.fixture(scope="session", autouse=True)
def delete_random_collection(patch_settings, dburi, random_collection_name):
    yield None
    mongo = MongoClient(dburi)
    mongodb = mongo[settings.DB_NAME]
    mongodb.drop_collection(random_collection_name)


@pytest.fixture(scope="session", autouse=True)
def testsettings(monkeypatch_session, dburi):
    return settings


@pytest.fixture
def testclient(dburi):
    with TestClient(app) as client:
        yield client
