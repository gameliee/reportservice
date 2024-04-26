import json
import uuid
import pytest
from datetime import datetime
from fastapi.testclient import TestClient
from .test_router_content import PREFIX as CONTENT_PREFIX

PREFIX = "/task"


@pytest.fixture(scope="module")
def fakecontentid(testclient):
    testid = str(uuid.uuid4())
    payload = json.dumps(
        {
            "_id": testid,
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

    response = testclient.post(f"{CONTENT_PREFIX}/", data=payload)
    assert response.status_code == 201
    yield testid
    response = testclient.delete(f"{CONTENT_PREFIX}/{testid}")
    assert response.status_code == 204


def test_create_task(testclient, fakecontentid: str):
    payload = json.dumps(
        {
            "actual_sent": "false",
            "content_id": fakecontentid,
            "description": "just an example task",
            "name": "My important task",
            "retries": 1,
            "trigger": {"cron": "* * * * *"},
        }
    )
    response = testclient.post(f"{PREFIX}/", data=payload)
    assert response.status_code == 201, response.json()
    testid = response.json()["_id"]
    response = testclient.delete(f"{PREFIX}/{testid}")
    assert response.status_code == 204, response.json()


@pytest.fixture(scope="module")
def createtesttask(testclient, fakecontentid: str):  # noqa: F811
    payload = json.dumps(
        {
            "actual_sent": "false",
            "content_id": fakecontentid,
            "description": "just an example task",
            "name": "My important task",
            "timeout": 1,
            "trigger": {"cron": "* * * * *"},
        }
    )
    response = testclient.post(f"{PREFIX}/", data=payload)
    assert response.status_code == 201, response.json()
    testid = response.json()["_id"]
    yield testid
    response = testclient.delete(f"{PREFIX}/{testid}")
    assert response.status_code == 204, response.json()


def test_content_get_tasks(testclient: TestClient, createtesttask: str, fakecontentid: str):
    response = testclient.get(f"{CONTENT_PREFIX}/{fakecontentid}/tasks")
    assert response.status_code == 200
    taskids = response.json()
    assert len(taskids) == 1
    taskid = taskids[0]
    assert taskid == createtesttask


def test_list_tasks(testclient: TestClient):
    response = testclient.get(f"{PREFIX}/")
    assert response.status_code == 200


def test_read_task1(testclient: TestClient):
    response = testclient.get(f"{PREFIX}/non")
    assert response.status_code == 404


def test_read_task2(testclient: TestClient, createtesttask: str):
    response = testclient.get(f"{PREFIX}/{createtesttask}")
    assert response.status_code == 200


def test_create_task1(testclient: TestClient):
    payload = json.dumps(
        {
            "actual_sent": "false",
            "content_id": "1112131415161718191A1B1C1D1E1F",
            "description": "just an example task",
            "name": "My important task",
            "timeout": 1,
            "trigger": {"cron": "* * * * *"},
        }
    )
    response = testclient.post(f"{PREFIX}/", data=payload)
    assert response.status_code == 404


def test_create_task2(testclient: TestClient):
    payload = json.dumps(
        {
            "actual_sent": "false",
            "content_id": "1112131415161718191A1B1C1D1E1F",
            "description": "just an example task",
            "name": "My important task",
            "timeout": 1,
            "trigger": {"interval": 1, "start_time": "2025-01-01 00:00:00"},
        }
    )
    response = testclient.post(f"{PREFIX}/", data=payload)
    assert response.status_code == 404


def test_create_task3(testclient: TestClient):
    payload = json.dumps(
        {
            "actual_sent": "false",
            "content_id": "1112131415161718191A1B1C1D1E1F",
            "description": "just an example task",
            "name": "My important task",
            "timeout": 1,
            "trigger": {"run_date": "2025-01-01 00:00:00"},
        }
    )
    response = testclient.post(f"{PREFIX}/", data=payload)
    assert response.status_code == 404


def test_create_task4(testclient: TestClient):
    payload = json.dumps(
        {
            "actual_sent": "false",
            "content_id": "1112131415161718191A1B1C1D1E1F",
            "description": "just an example task",
            "name": "My important task",
            "timeout": 1,
            "trigger": {},
        }
    )
    response = testclient.post(f"{PREFIX}/", data=payload)
    assert response.status_code == 422


def test_create_task5(testclient: TestClient, createtesttask: str):
    payload = json.dumps(
        {
            "_id": createtesttask,
            "actual_sent": "false",
            "content_id": "1112131415161718191A1B1C1D1E1F",
            "description": "just an example task",
            "name": "My important task",
            "timeout": 1,
            "trigger": {"cron": "* * * * *"},
        }
    )
    response = testclient.post(f"{PREFIX}/", data=payload)
    assert response.status_code == 404


def test_create_task6(testclient: TestClient, createtesttask: str):
    payload = json.dumps(
        {
            "_id": createtesttask,
            "actual_sent": "false",
            "content_id": "1112131415161718191A1B1C1D1E1F",
            "description": "just an example task",
            "name": "My important task",
            "timeout": 1,
            "trigger": {"cron": "* * * * linhtinh"},
        }
    )
    response = testclient.post(f"{PREFIX}/", data=payload)
    assert response.status_code == 422


def test_list_tasks2(testclient: TestClient):
    response = testclient.get(f"{PREFIX}/")
    assert response.status_code == 200


def test_delete_task(testclient: TestClient):
    response = testclient.get(f"{PREFIX}/empty")
    assert response.status_code == 404


def test_update_task(testclient: TestClient, createtesttask: str):
    payload = json.dumps({"description": "super duper informative description"})
    response = testclient.put(f"{PREFIX}/{createtesttask}", data=payload)
    assert response.status_code == 200


def test_update_task_trigger1(testclient: TestClient, createtesttask: str):
    payload = json.dumps({"trigger": {"interval": 1, "start_time": "2025-01-01 00:00:00"}})
    response = testclient.put(f"{PREFIX}/{createtesttask}", data=payload)
    assert response.status_code == 200
    ret = response.json()
    assert ret["trigger"]["type"] == "interval"
    assert ret["trigger"]["interval"] == 1
    # always pause after update trigger
    assert ret["enable"] is False
    assert ret["job"]["running"] is False
    assert ret["job"]["next_run_time"] is None


def test_update_task_trigger2(testclient: TestClient, createtesttask: str):
    payload = json.dumps({"trigger": {"run_date": "2025-01-01 00:00:00"}})
    response = testclient.put(f"{PREFIX}/{createtesttask}", data=payload)
    assert response.status_code == 200
    ret = response.json()
    assert ret["trigger"]["type"] == "date"
    assert datetime.fromisoformat(ret["trigger"]["run_date"]) == datetime.fromisoformat("2025-01-01 00:00:00")
    # always pause after update trigger
    assert ret["enable"] is False
    assert ret["job"]["running"] is False
    assert ret["job"]["next_run_time"] is None


def test_update_task_trigger3(testclient: TestClient, createtesttask: str):
    payload = json.dumps({"trigger": {"cron": "59 23 * * *"}})
    response = testclient.put(f"{PREFIX}/{createtesttask}", data=payload)
    assert response.status_code == 200
    ret = response.json()
    assert ret["trigger"]["cron"] == "59 23 * * *"
    assert len(ret["trigger"]["exclude_dates"]) == 0
    # always pause after update trigger
    assert ret["enable"] is False
    assert ret["job"]["running"] is False
    assert ret["job"]["next_run_time"] is None


def test_resume_task_after_update(testclient: TestClient, createtesttask: str):
    response = testclient.get(f"{PREFIX}/{createtesttask}/resume")
    assert response.status_code == 200
    ret = response.json()
    assert ret["enable"] is True
    assert ret["job"]["running"] is True
    next_run_time = ret["job"]["next_run_time"]
    next_run_time = datetime.fromisoformat(next_run_time)
    assert next_run_time.utcoffset().total_seconds() == 7 * 3600
    assert next_run_time.hour == 23
    assert next_run_time.minute == 59
    assert next_run_time.second == 0


def test_update_task_trigger4(testclient: TestClient, createtesttask: str):
    payload = json.dumps({"trigger": "wrong 23 * * *"})
    response = testclient.put(f"{PREFIX}/{createtesttask}", data=payload)
    assert response.status_code == 422


def test_pause_task(testclient: TestClient, createtesttask: str):
    response = testclient.get(f"{PREFIX}/{createtesttask}/pause")
    assert response.status_code == 200
    ret = response.json()
    assert ret["enable"] is False
    assert ret["job"]["running"] is False
    assert ret["job"]["next_run_time"] is None


def test_resume_task(testclient: TestClient, createtesttask: str):
    response = testclient.get(f"{PREFIX}/{createtesttask}/resume")
    assert response.status_code == 200
    ret = response.json()
    assert ret["enable"] is True
    assert ret["job"]["running"] is True
    next_run_time = ret["job"]["next_run_time"]
    next_run_time = datetime.fromisoformat(next_run_time)
    assert next_run_time.utcoffset().total_seconds() == 7 * 3600
    assert next_run_time.hour == 23
    assert next_run_time.minute == 59
    assert next_run_time.second == 0


def test_search_task(testclient: TestClient, createtesttask: str):
    payload = {"name": "My important task"}
    response = testclient.post(f"{PREFIX}/search", json=payload)
    assert response.status_code == 200
    ret = response.json()
    assert len(ret) == 1
    assert ret[0]["_id"] == createtesttask


def test_next_runtime(testclient: TestClient, createtesttask: str):
    payload = {"next_run_time": "2025-01-01 00:00:00"}
    response = testclient.put(f"{PREFIX}/{createtesttask}", json=payload)
    assert response.status_code == 200, response.json()
    ret = response.json()
    assert ret["enable"] is True
    assert ret["job"]["running"] is True
    next_run_time = ret["job"]["next_run_time"]
    next_run_time = datetime.fromisoformat(next_run_time)
    assert next_run_time.utcoffset().total_seconds() == 7 * 3600
    assert next_run_time.year == 2025
    assert next_run_time.month == 1
    assert next_run_time.day == 1
    assert next_run_time.hour == 0
    assert next_run_time.minute == 0
    assert next_run_time.second == 0
