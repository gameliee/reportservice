import json
import pytest
from fastapi.testclient import TestClient
from .test_router_config import generate_conf, true_config

PREFIX = "/stat"


@pytest.fixture
def _payload(test_time):
    begin, end = test_time
    payload = {"begin": begin.isoformat(), "end": end.isoformat()}
    return payload


def test_api_get_inout_count(testclient: TestClient, _payload, generate_conf):  # noqa: F811
    response = testclient.get(f"{PREFIX}/inout", params=_payload)
    assert "2" == response.text
    assert response.status_code == 200


def test_api_get_people_count(testclient: TestClient, _payload, generate_conf):  # noqa: F811
    response = testclient.get(f"{PREFIX}/people", params=_payload)
    assert response.text == "3"
    assert response.status_code == 200


def test_api_get_dataframe(testclient: TestClient, _payload, generate_conf):  # noqa: F811
    body = ["abc"]
    response = testclient.post(f"{PREFIX}/dataframe", params=_payload, data=json.dumps(body))
    assert response.status_code == 200, response.text
