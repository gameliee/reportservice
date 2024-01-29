import logging
from enum import IntEnum
import bson
import json
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


class LogLevelEnum(IntEnum):
    CRITICAL = logging.CRITICAL
    FATAL = logging.FATAL
    ERROR = logging.ERROR
    WARNING = logging.WARNING
    WARN = logging.WARN
    INFO = logging.INFO
    DEBUG = logging.DEBUG
    NOTSET = logging.NOTSET


class LogMeta(BaseModel):
    """the log metadata, also use as metadata in mongodb timeseries"""

    uid: Optional[str] = Field(None, description="could be the id of content or task")
    level: LogLevelEnum = Field(LogLevelEnum.NOTSET, description="log level")


class LogModel(BaseModel):
    logtime: datetime
    metadata: LogMeta
    message: str

    def myencode(self) -> dict:
        """encode for use with mongo's insert_one
        logtime must be a object of type bson.DatetimeMS
        other fields should be json encoded (note that enum is not supported)
        """
        dd = json.loads(self.model_dump_json())
        dd["logtime"] = bson.DatetimeMS(self.logtime)
        return dd
