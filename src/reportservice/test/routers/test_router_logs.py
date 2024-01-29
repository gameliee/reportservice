import json
import pytest
from fastapi.testclient import TestClient

PREFIX = "/log"


def test_get_log(testclient: TestClient):
    response = testclient.get(f"{PREFIX}/")
    assert response.status_code == 200
