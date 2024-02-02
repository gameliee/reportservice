from enum import Enum
from typing import Optional, List, Annotated, Literal, Union
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict, NonNegativeInt, AwareDatetime, model_validator
from apscheduler.job import Job
from ..models import TaskModelBase, TriggerModel, ContentModel


class TriggerModelType(str, Enum):
    CRON = "cron"
    INTERVAL = "interval"
    DATE = "date"
    INVALID = "invalid"


class TriggerModelBase(TriggerModel):
    jitter: Optional[NonNegativeInt] = Field(None, description="jitter")
    timeout: Optional[NonNegativeInt] = Field(60, description="timeout in seconds")


class CronTriggerModel(TriggerModelBase):
    # NOTE: fix that the default value of type is not set to TriggerModelType.CRON

    type: Literal[TriggerModelType.CRON] = Field(default=TriggerModelType.CRON, description="trigger type")
    cron: str = Field(..., description="cron string")
    start_date: Optional[AwareDatetime] = Field(None, description="start date")
    end_date: Optional[AwareDatetime] = Field(None, description="end date")
    exclude_dates: Optional[List[AwareDatetime]] = Field([], description="exclude date")

    @model_validator(mode="after")
    def validate_end_date(self) -> "CronTriggerModel":
        if self.start_date and self.end_date and self.end_date < self.start_date:
            raise ValueError("end_date should be greater than or equal to start_date")
        return self


class IntervalTriggerModel(TriggerModelBase):
    type: Literal[TriggerModelType.INTERVAL] = Field(default=TriggerModelType.INTERVAL, description="trigger type")
    interval: NonNegativeInt = Field(..., description="interval in seconds")
    start_time: datetime = Field(..., description="start time")
    exclude_dates: Optional[List[datetime]] = Field([], description="exclude date")


class DateTriggerModel(TriggerModelBase):
    type: Literal[TriggerModelType.DATE] = Field(default=TriggerModelType.DATE, description="trigger type")
    run_date: datetime = Field(..., description="run date")


class JobModel(BaseModel):
    pending: bool = Field(description="if a job is in pending state, it have not be stored into job storage")
    running: bool
    next_run_time: Optional[datetime]

    def parse_job(job: Job) -> "JobModel":
        jobmodel = JobModel(pending=job.pending, next_run_time=job.next_run_time, running=False)
        jobmodel.running = True if job.next_run_time else False
        return jobmodel


TriggerType = Annotated[
    Union[CronTriggerModel, IntervalTriggerModel, DateTriggerModel], Field(union_mode="left_to_right")
]


class TaskModelUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    enable: Optional[bool] = None
    timeout: Optional[int] = None
    trigger: Optional[TriggerType] = None
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "description": "super duper informative description for the task",
            }
        }
    )


class TaskModelView(TaskModelBase):
    """TaskModel for viewing"""

    trigger: TriggerType
    model_config = ConfigDict(arbitrary_types_allowed=True)
    content: ContentModel
    job: JobModel


class TaskModelCreate(TaskModelBase):
    trigger: TriggerType
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "name": "My important task",
                "description": "just an example task",
                "trigger": {"cron": "* * * * *"},
                "timeout": 1,
                "content_id": "1112131415161718191A1B1C1D1E1F",
                "enable": "false",
            }
        }
    )


# TriggerModel = Union[CronTriggerModel, IntervalTriggerModel, DateTriggerModel]
