from typing import Optional
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict
from apscheduler.job import Job
from ..models import TaskModelBase, TriggerModel, ContentModel


class JobModel(BaseModel):
    pending: bool = Field(description="if a job is in pending state, it have not be stored into job storage")
    running: bool
    next_run_time: Optional[datetime]

    def parse_job(job: Job) -> "JobModel":
        jobmodel = JobModel(pending=job.pending, next_run_time=job.next_run_time, running=False)
        jobmodel.running = True if job.next_run_time else False
        return jobmodel


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
