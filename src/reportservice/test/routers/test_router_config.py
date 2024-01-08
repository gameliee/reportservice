import json
import pytest
from fastapi.testclient import TestClient

PREFIX = "/config"
created = [False, 0]


@pytest.fixture
def settings_true(collectionsetttings, stmpsettings):
    return {"faceiddb": collectionsetttings, "smtp": stmpsettings}


@pytest.fixture
def generate_setting(testclient: TestClient, settings_true):
    if created[0] is False:
        payload = json.dumps(settings_true)
        response = testclient.post(f"{PREFIX}/", data=payload)
        assert response.status_code == 201
        created[0] = True
    assert created[0] is True


@pytest.fixture(scope="session")
def delete_old_settings(testclient: TestClient) -> None:
    response = testclient.delete(f"{PREFIX}/")
    assert response.status_code == 200 or response.status_code == 404


def test_get_settings1(testclient: TestClient, delete_old_settings):
    response = testclient.get(f"{PREFIX}/")
    assert response.status_code == 404


def test_update_settings1(testclient: TestClient, delete_old_settings):
    payload = json.dumps({"smtp": {"username": "noway"}})
    response = testclient.put(f"{PREFIX}/", data=payload)
    assert response.status_code == 404


def test_delete_settings(testclient: TestClient, delete_old_settings):
    response = testclient.delete(f"{PREFIX}/")
    assert response.status_code == 404


def test_get_settings(testclient: TestClient, delete_old_settings, generate_setting):
    response = testclient.get(f"{PREFIX}/")
    assert response.status_code == 200


def test_update_settings2(testclient: TestClient, delete_old_settings, generate_setting):
    payload = json.dumps(
        {
            "something": {
                "account": "testnvlazada@example.com",
            },
        }
    )
    response = testclient.put(f"{PREFIX}/", data=payload)
    assert response.status_code == 422


def test_update_settings3(testclient: TestClient, delete_old_settings, generate_setting, stmpsettings):
    payload = json.dumps({"faceiddb": {"user": "user"}, "smtp": stmpsettings})
    response = testclient.put(f"{PREFIX}/", data=payload)
    assert response.status_code == 422


def test_update_settings4(testclient: TestClient, delete_old_settings, generate_setting, collectionsetttings):
    payload = json.dumps(
        {
            "faceiddb": collectionsetttings,
            "smtp": {
                "account": "testnvlazada@example.com",
            },
        }
    )
    response = testclient.put(f"{PREFIX}/", data=payload)
    assert response.status_code == 200, response.json()


def test_delete_settings2(testclient: TestClient, delete_old_settings, generate_setting):
    response = testclient.delete(f"{PREFIX}/")
    assert response.status_code == 200
    created[0] = False
    assert created[0] is False
