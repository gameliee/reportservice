from random import randint
from datetime import datetime, timedelta, timezone
import pickle
from apscheduler.triggers.cron import CronTrigger
from ..customtriggers import CronTriggerWithHoliday, IntervalTriggerWithHoliday


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
