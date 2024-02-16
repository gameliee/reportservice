import json
import uuid
from datetime import datetime
import pytest
from fastapi.testclient import TestClient

PREFIX = "/content"


@pytest.fixture(scope="session")
def createtestcontent(testclient, generate_conf):  # noqa: F811
    payload = json.dumps(
        {
            "name": "test content",
            "description": "just an example content",
            "to": ["example@example.com"],
            "checkin_begin": "2000-01-01 07:00:00",
            "checkin_duration": "PT2H",
            "checkout_begin": "2000-01-01 17:00:00",
            "checkout_duration": "PT2H",
            "subject_template": "please use {{year}}",
            "body_template": "please use {{people_count}}",
            "attach_name_template": "{{year}}{{month}}{{date}}-{{hour}}{{min}}{{sec}}.xlsx",
        }
    )
    response = testclient.post(f"{PREFIX}/", data=payload)
    assert response.status_code == 201
    testcontentid = response.json()["_id"]
    yield testcontentid
    response = testclient.delete(f"{PREFIX}/{testcontentid}")
    assert response.status_code == 200


def test_list_contents(testclient: TestClient):
    response = testclient.get(f"{PREFIX}/")
    assert response.status_code == 200


def test_get_content1(testclient: TestClient):
    # testcase: get a non-exist content
    response = testclient.get(f"{PREFIX}/non")
    assert response.status_code == 404, response.json()


def test_create_duplicated_content(testclient: TestClient, createtestcontent: str):
    # testcase: create a duplicated content
    payload = json.dumps(
        {
            "_id": createtestcontent,
            "name": "example content",
            "description": "just an example content",
            "to": ["example@example.com"],
            "checkin_begin": "2000-01-01 07:00:00",
            "checkin_duration": "PT2H",
            "checkout_begin": "2000-01-01 17:00:00",
            "checkout_duration": "PT2H",
            "subject_template": "please use {{year}}",
            "body_template": "please use {{people_count}}",
            "attach_name_template": "{{year}}{{month}}{{date}}-{{hour}}{{min}}{{sec}}.xlsx",
        }
    )

    response = testclient.post(f"{PREFIX}/", data=payload)
    assert response.status_code == 404, response.json()


def test_get_content2(testclient: TestClient, createtestcontent: str):
    response = testclient.get(f"{PREFIX}/{createtestcontent}")
    assert response.status_code == 200, response.json()
    content = response.json()
    assert content["_id"] == createtestcontent


def test_download_excel1(testclient: TestClient, createtestcontent: str):
    response = testclient.get(f"{PREFIX}/{createtestcontent}/download")
    assert response.status_code == 404


def test_content_get_tasks1(testclient: TestClient, createtestcontent: str):
    # testcase: no task
    task_id = str(uuid.uuid4())
    response = testclient.get(f"{PREFIX}/{task_id}/tasks")
    assert response.status_code == 404, response.json()


def test_upload_excel_fail(testclient: TestClient, createtestcontent: str, excelfile):
    payload = {}
    files = [
        (
            "excelfile",
            (
                "docker-compose-pg.yml",
                open(excelfile, "rb"),
                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            ),
        )
    ]
    headers = {"Accept": "application/json"}

    response = testclient.post(f"{PREFIX}/{createtestcontent}/upload", headers=headers, data=payload, files=files)
    assert response.text == "true"


def test_upload_excel(testclient: TestClient, createtestcontent: str, excelfile):
    payload = {}
    files = [
        (
            "excelfile",
            (
                "test.xlsx",
                open(excelfile, "rb"),
                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            ),
        )
    ]
    headers = {"Accept": "application/json"}

    response = testclient.post(f"{PREFIX}/{createtestcontent}/upload", headers=headers, data=payload, files=files)
    assert response.text == "true"


def test_download_excel2(testclient: TestClient, createtestcontent: str):
    response = testclient.get(f"{PREFIX}/{createtestcontent}/download")
    assert response.status_code == 200


def test_update_content(testclient: TestClient, createtestcontent: str):
    payload = json.dumps({"description": "change the description to this informative one"})
    response = testclient.put(f"{PREFIX}/{createtestcontent}", data=payload)
    assert response.status_code == 200


def test_query_content(
    testclient: TestClient, createtestcontent: str, renderdate: datetime, generate_conf  # noqa: F811
):
    response = testclient.get(f"{PREFIX}/{createtestcontent}/query", params={"query_date": renderdate})
    assert response.status_code == 200


def test_query_content_now(
    testclient: TestClient, createtestcontent: str, renderdate: datetime, generate_conf  # noqa: F811
):
    response = testclient.get(f"{PREFIX}/{createtestcontent}/query")
    assert response.status_code == 200


def test_render_content(
    testclient: TestClient, createtestcontent: str, renderdate: datetime, generate_conf  # noqa: F811
):
    response = testclient.get(f"{PREFIX}/{createtestcontent}/render", params={"render_date": renderdate})
    assert response.status_code == 200


def test_render_content_now(
    testclient: TestClient, createtestcontent: str, renderdate: datetime, generate_conf  # noqa: F811
):
    response = testclient.get(f"{PREFIX}/{createtestcontent}/render")
    assert response.status_code == 200


def test_render_and_send(
    testclient: TestClient, createtestcontent: str, renderdate: datetime, generate_conf  # noqa: F811
):
    response = testclient.get(f"{PREFIX}/{createtestcontent}/render_and_send", params={"render_date": renderdate})
    assert response.status_code == 200


def test_render_and_send_now(
    testclient: TestClient, createtestcontent: str, renderdate: datetime, generate_conf  # noqa: F811
):
    response = testclient.get(f"{PREFIX}/{createtestcontent}/render_and_send")
    assert response.status_code == 200


def test_upload_wrong_excel(testclient: TestClient, createtestcontent: str, invalidexcelfile):
    payload = {}
    files = [
        (
            "excelfile",
            (
                "invalid.xlsx",
                open(invalidexcelfile, "rb"),
                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            ),
        )
    ]
    headers = {"Accept": "application/json"}

    with pytest.raises(Exception):
        response = testclient.post(f"{PREFIX}/{createtestcontent}/upload", headers=headers, data=payload, files=files)
        assert response.code == 400


def test_update_content2(testclient: TestClient, createtestcontent: str):
    payload = json.dumps({"attach": "true", "description": "change the description to this informative one"})
    response = testclient.put(f"{PREFIX}/{createtestcontent}", data=payload)
    assert response.status_code == 200


def test_upload_excel_again(testclient: TestClient, createtestcontent: str, excelfile):
    payload = {}
    files = [
        (
            "excelfile",
            (
                "test.xlsx",
                open(excelfile, "rb"),
                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            ),
        )
    ]
    headers = {"Accept": "application/json"}

    response = testclient.post(f"{PREFIX}/{createtestcontent}/upload", headers=headers, data=payload, files=files)
    assert response.text == "true"


def test_render_content2(
    testclient: TestClient, createtestcontent: str, renderdate: datetime, generate_conf  # noqa: F811
):
    response = testclient.get(f"{PREFIX}/{createtestcontent}/render", params={"render_date": renderdate})
    assert response.status_code == 200, response.json()


def test_get_tasks2(testclient: TestClient, createtestcontent: str):
    response = testclient.get(f"{PREFIX}/{createtestcontent}/tasks")
    assert response.status_code == 200, response.json()
    assert response.json() == []
