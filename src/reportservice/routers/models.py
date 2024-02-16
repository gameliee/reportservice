"""Common Classes for the report service"""
from typing import Annotated
from .stat import QueryParamters


ContentId = Annotated[str, "content_id"]
TaskId = Annotated[str, "task_id"]
