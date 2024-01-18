"""test the usecase send report to VT"""
import json
import pytest
from .test_router_config import generate_conf, true_config


def test_create_usecase(testclient, generate_conf, interest, send_to, send_cc):  # noqa: F811
    # First create content
    content_payload = json.dumps(
        {
            "name": "report_vt",
            "description": "report_vtcontent",
            "to": send_to,
            "checkin_begin": "2000-01-01 07:00:00",
            "checkin_duration": "PT2H",
            "checkout_begin": "2000-01-01 17:00:00",
            "checkout_duration": "PT2H",
            "subject_template": "please use {{year}}",
            "body_template": "please use {{people_count}}",
            "attach_name_template": "{{year}}{{month}}{{date}}-{{hour}}{{min}}{{sec}}.xlsx",
            "query_parameters": {"staffcodes": interest},
        }
    )
    response = testclient.post("/content/", data=content_payload)
    assert response.status_code == 201, response.json()
    content_id = response.json()["_id"]

    # Then create task
    task_payload = json.dumps(
        {
            "actual_sent": True,
            "content_id": content_id,
            "description": "report_vt task",
            "name": "report_vt",
            "timeout": 30,
            "trigger": {"cron": "* * * * *"},
        }
    )
    response = testclient.post("/task/", data=task_payload)
    assert response.status_code == 201, response.json()
    task_id = response.json()["_id"]

    # Get the task
    response = testclient.get(f"/task/{task_id}")
    assert response.status_code == 200, response.json()
    response_data = response.json()
    assert response_data["job"]["pending"] is False, response_data
    assert response_data["job"]["running"] is False, response_data
    assert response_data["job"]["next_run_time"] is None, response_data

    # resume the task
    response = testclient.get(f"/task/{task_id}/resume")
    assert response.status_code == 200, response.json()
    response_data = response.json()
    assert response_data["job"]["pending"] is False, response_data
    assert response_data["job"]["running"] is True, response_data
    assert response_data["job"]["next_run_time"] is not None, response_data

    # run the content now
    response = testclient.get(f"/content/{content_id}/render_and_send")
    assert response.status_code == 200, response.json()


def test_usecase_gdtt(testclient, generate_conf):  # noqa: F811
    # First create content
    content_payload = json.dumps(
        {
            "name": "report_gdtt",
            "description": "report_gdtt content",
            "to": ["giamdoc@example.com"],
            "checkin_begin": "2000-01-01 07:00:00",
            "checkin_duration": "PT2H",
            "checkout_begin": "2000-01-01 17:00:00",
            "checkout_duration": "PT2H",
            "subject_template": "Report for C5 {{year}}",
            "body_template": "please use {{people_count}}",
            "attach_name_template": "{{year}}{{month}}{{date}}-{{hour}}{{min}}{{sec}}.xlsx",
            "query_parameters": {"unit": ["C5", "Trung tâm C5"]},
        }
    )
    response = testclient.post("/content/", data=content_payload)
    assert response.status_code == 201, response.json()
    content_id = response.json()["_id"]

    # Then create task
    task_payload = json.dumps(
        {
            "actual_sent": True,
            "content_id": content_id,
            "description": "report_gdtt task",
            "name": "report_gdtt",
            "timeout": 30,
            "trigger": {"cron": "* * * * *"},
        }
    )
    response = testclient.post("/task/", data=task_payload)
    assert response.status_code == 201, response.json()
    task_id = response.json()["_id"]

    # Get the task
    response = testclient.get(f"/task/{task_id}")
    assert response.status_code == 200, response.json()
    response_data = response.json()
    assert response_data["job"]["pending"] is False, response_data
    assert response_data["job"]["running"] is False, response_data
    assert response_data["job"]["next_run_time"] is None, response_data

    # resume the task
    response = testclient.get(f"/task/{task_id}/resume")
    assert response.status_code == 200, response.json()
    response_data = response.json()
    assert response_data["job"]["pending"] is False, response_data
    assert response_data["job"]["running"] is True, response_data
    assert response_data["job"]["next_run_time"] is not None, response_data

    # run the content now
    response = testclient.get(f"/content/{content_id}/render_and_send")
    assert response.status_code == 200, response.json()


@pytest.fixture
def send_to():
    return ["hadtt30@example.com"]


@pytest.fixture
def send_cc():
    return ["tramnn3@example.com", "tcld_anhvhp@example.com"]


@pytest.fixture
def interest():
    staffcodes = [
        "003971",
        "001633",
        "123710",
        "206469",
        "199833",
        "059885",
        "080105",
        "140293",
        "052837",
        "000541",
        "185273",
        "088318",
        "091599",
        "048074",
        "007296",
        "123431",
        "211419",
        "187715",
        "206795",
        "187714",
        "197810",
        "206892",
        "187733",
        "141934",
        "199603",
        "187713",
        "054634",
        "187016",
        "206903",
        "230063",
        "215815",
        "087203",
        "178233",
        "226279",
        "207457",
        "222156",
        "180717",
        "095496",
        "102876",
        "269206",
        "205107",
        "186818",
        "144353",
        "224510",
        "199734",
        "225749",
        "047513",
        "204767",
        "204771",
        "108998",
        "164982",
        "187013",
        "059525",
        "185499",
        "178294",
        "087317",
        "105757",
        "206424",
        "207745",
        "220560",
        "087343",
        "194742",
        "209291",
        "060969",
        "095016",
        "200933",
        "199791",
        "201060",
        "218727",
        "204764",
        "205214",
        "206404",
        "204322",
        "206771",
        "208389",
        "209293",
        "206400",
        "199794",
        "207691",
        "208452",
        "208304",
        "212394",
        "204633",
        "207690",
        "206881",
        "232508",
        "087214",
        "087321",
        "122352",
        "215812",
        "207117",
        "207115",
        "009032",
        "009953",
        "001054",
        "249649",
        "120099",
        "087324",
        "109841",
        "118418",
        "121067",
        "207746",
        "100598",
        "139133",
    ]

    return staffcodes
