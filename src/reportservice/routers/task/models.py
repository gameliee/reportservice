import uuid
from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel, EmailStr, Field, ConfigDict
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


class TaskModelUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    trigger: Optional[str] = None
    timeout: Optional[int] = None
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "description": "super duper informative description",
            }
        }
    )


class TaskModelBase(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    # these id are fixed, never change them
    id: str = Field(default_factory=uuid.uuid4, alias="_id")
    job_id: str = Field(default_factory=uuid.uuid4, description="the jobid of apscheduler")
    content_id: str

    name: str = Field(...)
    description: Optional[str] = Field(None, description="Description")
    enable: bool = False  # by default, just add, don't send
    trigger: str = Field(description="cron string")
    timeout: int = Field(30, description="timeout in seconds")


class TaskModel(TaskModelBase):
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
                "trigger": "* * * * *",
                "timeout": 1,
                "content_id": "1112131415161718191A1B1C1D1E1F",
                "enable": "false",
            }
        }
    )
