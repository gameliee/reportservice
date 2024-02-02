import uuid
from enum import Enum
from typing import Optional, List, Annotated, Literal, Union
from datetime import datetime, timedelta
from fastapi import HTTPException, status
from pydantic import BaseModel, EmailStr, Field, ConfigDict, NonNegativeInt, AwareDatetime, model_validator
from pydantic.functional_validators import AfterValidator
from jinja2 import Environment, BaseLoader, Template
from jinja2.exceptions import TemplateSyntaxError
from .stat import QueryParamters

"""Content models"""


def validate_jinja(v: str) -> str:
    try:
        Environment(loader=BaseLoader).from_string(v)
    except TemplateSyntaxError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Jinja string error {e}")
    return v


JinjaStr = Annotated[str, AfterValidator(validate_jinja)]
ExcelAsStr = Annotated[str, "excel file in base64 string"]
ContentId = Annotated[str, "content_id"]
TaskId = Annotated[str, "task_id"]


class ContentModelBase(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    id: ContentId = Field(default_factory=uuid.uuid4, alias="_id")
    name: str = Field(description="Give it a memorable name")
    description: Optional[str] = Field(None, description="Description")
    to: List[EmailStr] = Field(min_length=1)
    cc: List[EmailStr] = []
    bcc: List[EmailStr] = []
    subject_template: JinjaStr
    body_template: JinjaStr
    attach: bool = False
    attach_name_template: JinjaStr = Field(
        "{{year}}{{month}}{{date}}.xlsx", description="filename to use when attach=True"
    )
    checkin_begin: datetime = Field(description="only the time part is interested, not the date part")
    checkin_duration: timedelta = Field("PT3H", description="ISO 8601 format for timedelta")
    checkout_begin: datetime = Field(description="only the time part is interested, not the date part")
    checkout_duration: timedelta = Field("PT3H", description="ISO 8601 format for timedelta")
    query_parameters: Optional[QueryParamters] = Field(
        None,
        description="query parameters for the report. If excel file present, the query parameters will be overrided.",
    )

    def get_subject_template(self) -> Template:
        return Environment(loader=BaseLoader).from_string(self.subject_template)

    def get_body_template(self) -> Template:
        return Environment(loader=BaseLoader).from_string(self.body_template)

    def get_attach_name_template(self) -> Template:
        return Environment(loader=BaseLoader).from_string(self.attach_name_template)


class ContentModel(ContentModelBase):
    excel: Optional[ExcelAsStr] = Field(None)

    def is_excel_uploaded(self):
        return self.excel is not None


"""Task models"""


class TriggerModelType(str, Enum):
    CRON = "cron"
    INTERVAL = "interval"
    DATE = "date"
    INVALID = "invalid"


class TriggerModelBase(BaseModel):
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


TriggerModel = Union[CronTriggerModel, IntervalTriggerModel, DateTriggerModel]


class TaskModelBase(BaseModel):
    model_config = ConfigDict(populate_by_name=True)
    id: TaskId = Field(
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
