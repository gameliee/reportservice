import json
import pytest
from fastapi.testclient import TestClient

PREFIX = "/config"


def test_update_conf6(testclient: TestClient):
    """update nothing to nothing"""
    payload = json.dumps({})
    response = testclient.put(f"{PREFIX}/", data=payload)
    assert response.status_code == 404


@pytest.fixture(scope="session")
def true_config(collectionconfig, smtpconfig):
    return {"faceiddb": collectionconfig, "smtp": smtpconfig}


@pytest.fixture(scope="session")
def generate_conf(testclient: TestClient, true_config):
    response = testclient.get(f"{PREFIX}/")
    if response.status_code == 404:
        payload = json.dumps(true_config)
        response = testclient.post(f"{PREFIX}/", data=payload)
        assert response.status_code == 201


def test_get_conf1(testclient: TestClient):
    response = testclient.get(f"{PREFIX}/")
    assert response.status_code == 404


def test_update_conf1(testclient: TestClient):
    payload = json.dumps({"smtp": {"username": "noway"}})
    response = testclient.put(f"{PREFIX}/", data=payload)
    assert response.status_code == 404


def test_generate_conf_again(testclient: TestClient, true_config, generate_conf):
    payload = json.dumps(true_config)
    response = testclient.post(f"{PREFIX}/", data=payload)
    assert response.status_code == 409, response.json()


def test_get_conf(testclient: TestClient, generate_conf):
    response = testclient.get(f"{PREFIX}/")
    assert response.status_code == 200


def test_update_conf2(testclient: TestClient, generate_conf):
    payload = json.dumps(
        {
            "something": {
                "account": "testnvlazada@example.com",
            },
        }
    )
    response = testclient.put(f"{PREFIX}/", data=payload)
    assert response.status_code == 422


def test_update_conf3(testclient: TestClient, generate_conf, smtpconfig):
    payload = json.dumps({"faceiddb": {"user": "user"}, "smtp": smtpconfig})
    response = testclient.put(f"{PREFIX}/", data=payload)
    assert response.status_code == 422


def test_update_conf4(testclient: TestClient, generate_conf, collectionconfig):
    payload = json.dumps(
        {
            "faceiddb": collectionconfig,
            "smtp": {
                "account": "testnvlazada@example.com",
            },
        }
    )
    response = testclient.put(f"{PREFIX}/", data=payload)
    assert response.status_code == 200, response.json()


def test_update_conf5(testclient: TestClient, generate_conf):
    """update nothing"""
    payload = json.dumps({})
    response = testclient.put(f"{PREFIX}/", data=payload)
    assert response.status_code == 200


def test_delete_conf2(testclient: TestClient, generate_conf):
    response = testclient.delete(f"{PREFIX}/")
    assert response.status_code == 405  # method not allowed
