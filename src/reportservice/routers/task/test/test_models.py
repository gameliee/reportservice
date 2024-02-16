import pytest
from datetime import datetime, timezone
from pydantic import ValidationError
from ..models import (
    TriggerModelType,
    CronTriggerModel,
    IntervalTriggerModel,
    DateTriggerModel,
    TaskModelBase,
    TaskModel,
    TaskModelUpdate,
    TaskModelCreate,
)


def test_cron_trigger_model():
    cron = "0 0 * * *"
    start_date = datetime(2022, 1, 1).astimezone()
    end_date = datetime(2022, 12, 31).astimezone()
    exclude_dates = [datetime(2022, 2, 14).astimezone(), datetime(2022, 4, 1).astimezone()]

    trigger = CronTriggerModel(
        jitter=5, cron=cron, start_date=start_date, end_date=end_date, exclude_dates=exclude_dates
    )
    assert trigger is not None
    assert trigger.type == TriggerModelType.CRON

    with pytest.raises(ValueError):
        CronTriggerModel(
            type="abc", jitter=5, cron=cron, start_date=start_date, end_date=end_date, exclude_dates=exclude_dates
        )

    with pytest.raises(ValueError):
        CronTriggerModel(jitter=5, cron=cron, start_date=end_date, end_date=start_date, exclude_dates=exclude_dates)

    CronTriggerModel(cron=cron)


def test_interval_trigger_model():
    interval = 60
    start_time = datetime(2022, 1, 1)

    IntervalTriggerModel(jitter=5, interval=interval, start_time=start_time)

    with pytest.raises(ValueError):
        IntervalTriggerModel(type="abc", jitter=5, interval=interval, start_time=start_time)

    with pytest.raises(ValueError):
        IntervalTriggerModel(jitter=5, interval=-1, start_time=start_time)


def test_date_trigger_model():
    run_date = datetime(2022, 1, 1)

    DateTriggerModel(jitter=5, run_date=run_date)

    with pytest.raises(ValueError):
        DateTriggerModel(type="abc", jitter=5, run_date=run_date)

    with pytest.raises(ValueError):
        DateTriggerModel(jitter=5, run_date=None)


@pytest.fixture
def goodtrigger():
    cron = "0 0 * * *"
    start_date = datetime(2022, 1, 1).astimezone()
    end_date = datetime(2022, 12, 31).astimezone()
    exclude_dates = [datetime(2022, 2, 14).astimezone(), datetime(2022, 4, 1).astimezone()]
    return CronTriggerModel(jitter=5, cron=cron, start_date=start_date, end_date=end_date, exclude_dates=exclude_dates)


def test_task_model_base(goodtrigger):
    content_id = "1112131415161718191A1B1C1D1E1F"

    TaskModelBase(
        content_id=content_id,
        name="My important task",
        description="just an example task",
        enable=False,
        timeout=1,
        trigger=goodtrigger,
    )

    with pytest.raises(ValidationError):
        TaskModelBase(
            content_id=content_id,
            name="My important task",
            description="just an example task",
            enable=False,
            timeout=1,
            trigger="* * * * *",
        )


def test_task_model(goodtrigger):
    content_id = "1112131415161718191A1B1C1D1E1F"

    task = TaskModel(
        content_id=content_id,
        name="My important task",
        description="just an example task",
        enable=False,
        timeout=1,
        trigger=goodtrigger,
    )

    # testcase: change frozen value
    with pytest.raises(ValidationError):
        task.id = "abc"


def test_task_model_update():
    update_data = {
        "name": "Updated task name",
        "description": "Updated task description",
        "enable": True,
        "timeout": 60,
        "trigger": {
            "type": "cron",
            "cron": "0 0 * * *",
            "start_date": "2022-01-01T00:00:00+00:00",
            "end_date": "2022-12-31T00:00:00+00:00",
            "exclude_dates": ["2022-02-14T00:00:00+00:00", "2022-04-01T00:00:00+00:00"],
        },
    }

    task_update = TaskModelUpdate(**update_data)

    assert task_update.name == "Updated task name"
    assert task_update.description == "Updated task description"
    assert task_update.enable is True
    assert task_update.timeout == 60
    assert isinstance(task_update.trigger, CronTriggerModel)
    assert task_update.trigger.type == TriggerModelType.CRON
    assert task_update.trigger.cron == "0 0 * * *"
    assert task_update.trigger.start_date == datetime(2022, 1, 1, tzinfo=timezone.utc)
    assert task_update.trigger.end_date == datetime(2022, 12, 31, tzinfo=timezone.utc)
    assert task_update.trigger.exclude_dates == [
        datetime(2022, 2, 14, tzinfo=timezone.utc),
        datetime(2022, 4, 1, tzinfo=timezone.utc),
    ]


def test_task_model_create_cron():
    create_data = {
        "name": "My important task",
        "description": "just an example task",
        "trigger": {"cron": "* * * * *"},
        "timeout": 1,
        "content_id": "1112131415161718191A1B1C1D1E1F",
        "enable": False,
    }

    task_create = TaskModelCreate(**create_data)

    assert task_create.name == "My important task"
    assert task_create.description == "just an example task"
    assert task_create.enable is False
    assert task_create.timeout == 1
    assert task_create.trigger.cron == "* * * * *"
    assert task_create.content_id == "1112131415161718191A1B1C1D1E1F"


def test_task_model_create_interval():
    create_data = {
        "name": "My important task",
        "description": "just an example task",
        "trigger": {"interval": 1, "start_time": "2022-01-01T00:00:00"},
        "content_id": "1112131415161718191A1B1C1D1E1F",
        "enable": True,
    }

    task_create = TaskModelCreate(**create_data)

    assert task_create.enable is True
    assert task_create.trigger.interval == 1
    assert task_create.trigger.start_time == datetime(2022, 1, 1)


def test_task_model_create_date():
    create_data = {
        "name": "My important task",
        "description": "just an example task",
        "trigger": {"run_date": "2022-01-01T00:00:00"},
        "content_id": "1112131415161718191A1B1C1D1E1F",
        "enable": True,
    }

    task_create = TaskModelCreate(**create_data)

    assert task_create.trigger.run_date == datetime(2022, 1, 1)
