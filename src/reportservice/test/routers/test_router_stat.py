import json
import pytest
from fastapi.testclient import TestClient

PREFIX = "/stat"


@pytest.fixture(scope="session")
def _payload(test_time):
    begin, end = test_time
    payload = {"begin": begin.isoformat(), "end": end.isoformat()}
    return payload


def test_api_get_inout_count(testclient: TestClient, _payload, generate_conf):  # noqa: F811
    response = testclient.get(f"{PREFIX}/count_inout", params=_payload)
    assert "2" == response.text
    assert response.status_code == 200, response.json()


def test_api_get_people_count(testclient: TestClient, _payload, generate_conf):  # noqa: F811
    response = testclient.get(f"{PREFIX}/count_people", params=_payload)
    assert response.text == "723"
    assert response.status_code == 200, response.json()


def test_api_get_people_inout(testclient: TestClient, _payload, generate_conf):  # noqa: F811
    body = {"staff_codes": ["abc"]}
    response = testclient.post(f"{PREFIX}/people_inout", params=_payload, data=json.dumps(body))
    assert response.status_code == 200, response.json()


def test_api_get_has_sample_count(testclient: TestClient, _payload, generate_conf):  # noqa: F811
    response = testclient.get(f"{PREFIX}/count_has_sample", params=_payload)
    assert response.text == "723"
    assert response.status_code == 200, response.json()


def test_api_get_should_checkinout_count(testclient: TestClient, _payload, generate_conf):  # noqa: F811
    response = testclient.get(f"{PREFIX}/count_should_checkinout", params=_payload)
    assert response.text == "721"
    assert response.status_code == 200, response.json()
