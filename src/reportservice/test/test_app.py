import pytest
from fastapi.testclient import TestClient


@pytest.mark.asyncio
async def test_healthcheck(testclient: TestClient):
    response = testclient.get("/")
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_version(testclient: TestClient):
    response = testclient.get("/version")
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_connection_status(testclient: TestClient):
    response = testclient.get("/connection-status")
    assert response.status_code == 200
