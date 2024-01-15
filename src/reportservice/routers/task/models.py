import uuid
from enum import Enum
from typing import Optional, List, Literal, Any, Union
from datetime import datetime
from abc import ABC, abstractmethod
from pydantic import (
    BaseModel,
    EmailStr,
    Field,
    ConfigDict,
    model_validator,
    NonNegativeInt,
    field_validator,
    create_model,
)
from apscheduler.job import Job
from ..content.models import ContentModel


class JobModel(BaseModel):
    pending: bool = Field(description="if a job is in pending state, it have not be stored into job")
    running: bool
    next_run_time: Optional[datetime]

    def parse_job(job: Job) -> "JobModel":
        jobmodel = JobModel(pending=job.pending, next_run_time=job.next_run_time, running=False)
        jobmodel.running = True if job.next_run_time else False
        return jobmodel


class TriggerModelType(str, Enum):
    CRON = "cron"
    INTERVAL = "interval"
    DATE = "date"
    INVALID = "invalid"


class TriggerModelBase(BaseModel, ABC):
    jitter: Optional[NonNegativeInt] = Field(None, description="jitter")


class CronTriggerModel(TriggerModelBase):
    # NOTE: fix that the default value of type is not set to TriggerModelType.CRON

    type: Literal[TriggerModelType.CRON] = Field(default=TriggerModelType.CRON, description="trigger type")
    cron: str = Field(..., description="cron string")
    start_date: Optional[datetime] = Field(None, description="start date")
    end_date: Optional[datetime] = Field(None, description="end date")
    exclude_dates: Optional[List[datetime]] = Field([], description="exclude date")

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


TriggerModel = Union[CronTriggerModel, IntervalTriggerModel, DateTriggerModel]


class TaskModelBase(BaseModel):
    model_config = ConfigDict(populate_by_name=True)
    id: str = Field(
        default_factory=uuid.uuid4,
        alias="_id",
        frozen=True,
        description="the id in the database of task, never attempt to change me",
    )
    job_id: str = Field(default_factory=uuid.uuid4, description="the jobid of apscheduler")
    content_id: str

    name: str = Field(...)
    description: Optional[str] = Field(None, description="Description")
    enable: bool = False  # by default, just add, don't send
    timeout: int = Field(30, description="timeout in seconds")
    trigger: TriggerModel = Field(..., description="trigger for this task")

    def __init__(self, **data):
        super().__init__(**data, id=str(uuid.uuid4()))


class TaskModelUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    enable: Optional[bool] = None
    timeout: Optional[int] = None
    trigger: Optional[TriggerModel] = None
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "description": "super duper informative description for the task",
            }
        }
    )


class TaskModelView(TaskModelBase):
    """TaskModel for viewing"""

    model_config = ConfigDict(arbitrary_types_allowed=True)
    content: ContentModel
    job: JobModel


class TaskModelCreate(TaskModelBase):
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
