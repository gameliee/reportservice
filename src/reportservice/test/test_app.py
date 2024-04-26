import pytest
from fastapi.testclient import TestClient


@pytest.mark.asyncio
async def test_healthcheck(testclient: TestClient):
    response = testclient.get("/")
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_healthcheck_profile(testclient: TestClient):
    response = testclient.get("/", params={"profile": "true"})
    assert response.status_code == 200
    assert "pyinstrument" in response.text
