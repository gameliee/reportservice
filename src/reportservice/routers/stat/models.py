"""data models"""
from enum import Enum
from typing import Annotated, Optional
from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field

StaffCodeStr = Annotated[str, "staff code"]


class QueryException(Exception):
    pass


class MongoSampleStateOfStaffModel(str, Enum):
    """Copy from SampelStateOfStaffModel"""

    no_sample = "no_sample"
    ready_to_checkin_checkout = "ready_to_checkin_checkout"


class MongoStateOfStaffModel(str, Enum):
    """Copy from WrokingStateOfStaffModel"""

    active = "active"
    on_leave = "on_leave"
    zombie = "zombie"


class MongoStaffModel(BaseModel):
    """Copy from ResponseData_StaffModelInResponse"""

    model_config = ConfigDict(extra="allow")
    staff_code: StaffCodeStr
    full_name: str
    sex: Optional[str]
    email: Optional[str]
    cellphone: str
    unit: Optional[str]
    department: Optional[str]
    title: Optional[str]
    sample_state: MongoSampleStateOfStaffModel
    working_state: MongoStateOfStaffModel


class MongoInOutModel(BaseModel):
    first_record: Optional[datetime] = Field(None, alias="first record in the database")
    last_record: Optional[datetime] = Field(None, alias="last record in the database")


class PersonInout(MongoStaffModel, MongoInOutModel):
    model_config = ConfigDict(extra="allow")


class PersonInoutCollection(BaseModel):
    count: int
    values: list[PersonInout]
