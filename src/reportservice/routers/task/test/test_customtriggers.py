import pytest
import time
from random import randint
from datetime import datetime, timedelta, timezone
import pickle
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.date import DateTrigger
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.job import Job
from ..models import JobModel
from ..customtriggers import CronTriggerWithHoliday, IntervalTriggerWithHoliday, CustomDateTrigger


def test_cron_trigger_with_holiday_behavior():
    random_minute = randint(0, 59)
    random_hour = randint(0, 23)
    random_day = randint(1, 28)
    random_month = randint(1, 12)
    random_weekday = randint(0, 6)
    cron = f"{random_minute} {random_hour} {random_day} {random_month} {random_weekday}"

    my_trigger = CronTriggerWithHoliday.from_crontab(cron)
    cron_trigger = CronTrigger.from_crontab(cron)

    # Test case 1: previous_fire_time is None, now is a datetime object
    previous_fire_time = None
    now = datetime.now()
    assert my_trigger.get_next_fire_time(previous_fire_time, now) == cron_trigger.get_next_fire_time(
        previous_fire_time, now
    )

    # Test case 2: previous_fire_time is a datetime object, now is a datetime object
    previous_fire_time = datetime(2021, 12, 31, 23, 59, 59)
    now = datetime(2022, 1, 1, 0, 0, 0)
    assert my_trigger.get_next_fire_time(previous_fire_time, now) == cron_trigger.get_next_fire_time(
        previous_fire_time, now
    )

    # Test case 3: previous_fire_time is a datetime object, now is a datetime object
    previous_fire_time = datetime(2022, 1, 1, 0, 0, 0)
    now = datetime(2022, 1, 1, 0, 0, 1)
    assert my_trigger.get_next_fire_time(previous_fire_time, now) == cron_trigger.get_next_fire_time(
        previous_fire_time, now
    )


def test_get_next_fire_time():
    # Create an instance of CronTriggerWithHoliday
    trigger = CronTriggerWithHoliday.from_crontab(
        "1 0 * * *"
    )  # just dont run this task at 00:00, the result will be wrong
    utc_dt = datetime.now(timezone.utc)  # UTC time
    now = utc_dt.astimezone()  # local time
    tomorrow = now + timedelta(days=1)
    tomorrow2 = now + timedelta(days=2)
    trigger.set_exclude_dates([tomorrow])

    # Test case 1: previous_fire_time is None, now is a datetime object
    previous_fire_time = None
    next_fire_time = trigger.get_next_fire_time(previous_fire_time, now)
    assert next_fire_time is not None
    assert next_fire_time.date() == tomorrow2.date()

    # Test case 2: previous_fire_time is a datetime object, now is a datetime object
    previous_fire_time = now - timedelta(seconds=1)
    next_fire_time = trigger.get_next_fire_time(previous_fire_time, now)
    assert next_fire_time is not None
    assert next_fire_time.date() == tomorrow2.date()


def test_serilize_cron_trigger_with_holiday():
    trigger = CronTriggerWithHoliday.from_crontab("* * * * *")
    assert trigger.exclude_dates == []
    serilized = pickle.dumps(trigger)
    deserialized = pickle.loads(serilized)
    assert isinstance(deserialized, CronTriggerWithHoliday)
    assert deserialized.exclude_dates == trigger.exclude_dates


def test_IntervalTrigger():
    start_date = datetime(2022, 1, 1, 23, 20, 0, 0).astimezone()
    now = datetime(2022, 1, 1, 23, 30, 0, 0).astimezone()
    trigger = IntervalTriggerWithHoliday(hours=1, start_date=start_date)
    next_fire_time = trigger.get_next_fire_time(None, now)
    assert next_fire_time.day == 2, next_fire_time
    assert next_fire_time.hour == 0, next_fire_time
    assert next_fire_time.minute == 20, next_fire_time

    trigger = IntervalTriggerWithHoliday(hours=1, start_date=start_date, exclude_dates=[datetime(2022, 1, 2, 1, 2, 3)])
    next_fire_time = trigger.get_next_fire_time(None, now)
    assert next_fire_time.day == 3, next_fire_time
    assert next_fire_time.hour == 0, next_fire_time
    assert next_fire_time.minute == 20, next_fire_time


def test_serilize_interval_trigger_with_holiday():
    start_date = datetime(2022, 1, 1, 23, 20, 0, 0).astimezone()
    trigger = IntervalTriggerWithHoliday(hours=1, start_date=start_date)
    serilized = pickle.dumps(trigger)
    deserialized = pickle.loads(serilized)
    assert isinstance(deserialized, IntervalTriggerWithHoliday)
    assert deserialized.exclude_dates == trigger.exclude_dates


@pytest.fixture
def scheduler():
    scheduler = BackgroundScheduler()
    scheduler.start()
    yield scheduler
    scheduler.shutdown()


def hello():
    print("hello")


def test_add_custom_datetrigger(scheduler: BackgroundScheduler):
    run_date = datetime.now() + timedelta(seconds=1)
    trigger = CustomDateTrigger(run_date=run_date)
    job1 = scheduler.add_job(hello, trigger=trigger)
    assert isinstance(job1.trigger, CustomDateTrigger)
    assert isinstance(job1.trigger, DateTrigger)
    job2: Job = scheduler.get_job(job_id=job1.id)
    assert job2 is not None
    assert isinstance(job2.trigger, CustomDateTrigger)
    assert isinstance(job2.trigger, DateTrigger)


def test_custom_datetrigger_behaviors(scheduler: BackgroundScheduler):
    # testcase 1: run_date is in the future, without timezone
    run_date = datetime.now() + timedelta(seconds=1)
    trigger = CustomDateTrigger(run_date=run_date)
    job1 = scheduler.add_job(hello, trigger=trigger)

    # testcase 2: run_date is in the future, with timezone
    utc_dt = datetime.now(timezone.utc)  # UTC time
    now = utc_dt.astimezone()  # local time
    run_date = now + timedelta(seconds=1)
    trigger = CustomDateTrigger(run_date=run_date)
    job2 = scheduler.add_job(hello, trigger=trigger)

    # wait for the job run
    time.sleep(2)
    # after trigger, job1 and job2 is NOT REMOVED. This is different than the default DateTrigger
    job1: Job = scheduler.get_job(job1.id)
    assert job1 is not None
    assert job1.next_run_time == CustomDateTrigger.VERY_BIG_DATE
    job2: Job = scheduler.get_job(job2.id)
    assert job2 is not None
    assert job2.next_run_time == CustomDateTrigger.VERY_BIG_DATE

    # testcase 3: run_date is in the past. In this case, CustomeDateTrigger and DateTrigger behave the same
    run_date = datetime.now() - timedelta(seconds=1)
    trigger = CustomDateTrigger(run_date=run_date)
    job3 = scheduler.add_job(hello, trigger=trigger)
    job3: Job = scheduler.get_job(job3.id)  # never been triggered
    assert job3 is not None
    assert job3.next_run_time.replace(tzinfo=None) == run_date

    run_date = datetime.now() - timedelta(seconds=1)
    trigger = DateTrigger(run_date=run_date)
    job4 = scheduler.add_job(hello, trigger=trigger)
    job4: Job = scheduler.get_job(job4.id)  # never been triggered
    assert job4 is not None
    assert job4.next_run_time.replace(tzinfo=None) == run_date


def test_parse_custom_datetrigger(scheduler: BackgroundScheduler):
    run_date = datetime.now() + timedelta(seconds=1)
    trigger = CustomDateTrigger(run_date=run_date)
    job = scheduler.add_job(hello, trigger=trigger)
    job1 = scheduler.get_job(job.id)
    assert job1 is not None
    jobmodel1: JobModel = JobModel.parse_job(job1)
    assert jobmodel1.running is True
    assert jobmodel1.next_run_time.replace(tzinfo=None) == run_date
    time.sleep(2)
    job2: Job = scheduler.get_job(job.id)
    assert job2 is not None
    jobmodel2: JobModel = JobModel.parse_job(job2)
    assert jobmodel2.running is False
    assert jobmodel2.next_run_time is None

    # test update the trigger as well
    trigger = IntervalTriggerWithHoliday(weeks=1, start_date=datetime.now())
    job2.reschedule(trigger)

    job3: Job = scheduler.get_job(job.id)
    assert job3 is not None
    assert isinstance(job3.trigger, IntervalTriggerWithHoliday)
    jobmodel3: JobModel = JobModel.parse_job(job3)
    assert jobmodel3.running is True
    assert jobmodel3.next_run_time is not None


@pytest.mark.skip(reason="pause and resume is not supported for CustomDateTrigger")
def test_custom_datetrigger_pause(scheduler: BackgroundScheduler):
    # testcase1: pause and resume before the run_date
    run_date = datetime.now() + timedelta(seconds=1)
    trigger = CustomDateTrigger(run_date=run_date)
    job1 = scheduler.add_job(hello, trigger=trigger)
    assert job1.next_run_time.replace(tzinfo=None) == run_date
    job1 = job1.pause()
    assert job1.next_run_time is None
    job1 = job1.resume()
    assert job1.next_run_time.replace(tzinfo=None) == run_date

    # testcase2: pause before the run_date and resume after the run_date
    run_date = datetime.now() + timedelta(seconds=1)
    trigger = CustomDateTrigger(run_date=run_date)
    job2 = scheduler.add_job(hello, trigger=trigger)
    assert job2.next_run_time.replace(tzinfo=None) == run_date
    job2 = job2.pause()
    assert job2.next_run_time is None
    time.sleep(2)
    job2 = job2.resume()
    assert job2.next_run_time is None

    # testcase3: pause and resume after the run_date
    run_date = datetime.now() + timedelta(seconds=1)
    trigger = CustomDateTrigger(run_date=run_date)
    job3 = scheduler.add_job(hello, trigger=trigger)
    assert job3.next_run_time.replace(tzinfo=None) == run_date
    time.sleep(2)
    job3 = job3.pause()
    assert job3.next_run_time is None
    job3 = job3.resume()
    assert job3.next_run_time is None
