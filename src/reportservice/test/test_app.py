from fastapi.testclient import TestClient


def test_healthcheck(testclient: TestClient):
    response = testclient.get("/")
    assert response.status_code == 200


def test_version(testclient: TestClient):
    response = testclient.get("/version")
    assert response.status_code == 200
