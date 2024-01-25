from typing import List
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger


class CronTriggerWithHoliday(CronTrigger):
    def __init__(
        self,
        year=None,
        month=None,
        day=None,
        week=None,
        day_of_week=None,
        hour=None,
        minute=None,
        second=None,
        start_date=None,
        end_date=None,
        timezone=None,
        jitter=None,
        exclude_dates=[],
    ):
        super().__init__(
            year=year,
            month=month,
            day=day,
            week=week,
            day_of_week=day_of_week,
            hour=hour,
            minute=minute,
            second=second,
            start_date=start_date,
            end_date=end_date,
            timezone=timezone,
            jitter=jitter,
        )
        if exclude_dates is None:
            exclude_dates = []
        if len(exclude_dates) > 0:
            exclude_dates = [d.date() for d in exclude_dates]
        self.exclude_dates = exclude_dates

    def set_exclude_dates(self, exclude_dates: List):
        if exclude_dates is None:
            exclude_dates = []
        if len(exclude_dates) > 0:
            exclude_dates = [d.date() for d in exclude_dates]
        self.exclude_dates = exclude_dates

    def get_next_fire_time(self, previous_fire_time, now):
        next_fire_time = super().get_next_fire_time(previous_fire_time, now)
        if self.exclude_dates is None or len(self.exclude_dates) == 0:
            return next_fire_time

        i = 0  # a counter to avoid infinite loop
        while next_fire_time is not None and next_fire_time.date() in self.exclude_dates:
            next_fire_time = super().get_next_fire_time(next_fire_time, next_fire_time)
            i += 1
            if i > 1000:
                raise Exception("Too many exclude dates")
        return next_fire_time

    def __getstate__(self):
        upper = super().__getstate__()
        upper["exclude_dates"] = self.exclude_dates
        return upper

    def __setstate__(self, state):
        super().__setstate__(state)
        self.exclude_dates = state.get("exclude_dates", [])


class IntervalTriggerWithHoliday(IntervalTrigger):
    def __init__(
        self,
        weeks=0,
        days=0,
        hours=0,
        minutes=0,
        seconds=0,
        start_date=None,
        end_date=None,
        timezone=None,
        jitter=None,
        exclude_dates=[],
    ):
        super().__init__(weeks, days, hours, minutes, seconds, start_date, end_date, timezone, jitter)
        if exclude_dates is None:
            exclude_dates = []
        if len(exclude_dates) > 0:
            exclude_dates = [d.date() for d in exclude_dates]
        self.exclude_dates = exclude_dates

    def get_next_fire_time(self, previous_fire_time, now):
        next_fire_time = super().get_next_fire_time(previous_fire_time, now)
        if self.exclude_dates is None or len(self.exclude_dates) == 0:
            return next_fire_time

        i = 0  # a counter to avoid infinite loop
        while next_fire_time is not None and next_fire_time.date() in self.exclude_dates:
            next_fire_time = super().get_next_fire_time(next_fire_time, next_fire_time)
            i += 1
            if i > 1000:
                raise Exception("Too many exclude dates")
        return next_fire_time

    def __getstate__(self):
        upper = super().__getstate__()
        upper["exclude_dates"] = self.exclude_dates
        return upper

    def __setstate__(self, state):
        super().__setstate__(state)
        self.exclude_dates = state.get("exclude_dates", [])
