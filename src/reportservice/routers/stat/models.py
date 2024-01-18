"""data models"""
from enum import Enum
from bson import json_util
import json
from typing import Annotated, Optional
from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field
from pydantic.functional_validators import AfterValidator

__all__ = [
    "QueryParamters",
    "QueryException",
    "PersonInout",
    "PersonInoutCollection",
]

StaffCodeStr = Annotated[str, "staff code"]
FullNameStr = Annotated[str, "full name"]
UnitStr = Annotated[str, "unit name"]
DepartmentStr = Annotated[str, "department name"]
TitleStr = Annotated[str, "title name"]
EmailStr = Annotated[str, "email address"]
CellphoneStr = Annotated[str, "cellphone number"]


def validate_query(query_string):
    # Attempt to parse the query string into a Python dictionary
    json.loads(query_string, object_hook=json_util.object_hook)
    return query_string


MongoQueryStr = Annotated[str, "mongo query string", AfterValidator(validate_query)]


class QueryParamters(BaseModel):
    """These parameters should be OR together"""

    staffcodes: list[StaffCodeStr] = []
    fullnames: list[FullNameStr] = []
    units: list[UnitStr] = []
    departments: list[DepartmentStr] = []
    titles: list[TitleStr] = []
    emails: list[EmailStr] = []
    cellphones: list[CellphoneStr] = []
    custom_queries: list[MongoQueryStr] = []

    def is_empty(self):
        return (
            len(self.staffcodes)
            + len(self.fullnames)
            + len(self.units)
            + len(self.departments)
            + len(self.titles)
            + len(self.emails)
            + len(self.cellphones)
            + len(self.custom_queries)
            == 0
        )


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
    """Reflect from ResponseData_StaffModelInResponse"""

    model_config = ConfigDict(extra="allow")
    staff_code: StaffCodeStr
    full_name: Optional[FullNameStr] = Field(None)
    sex: Optional[str] = Field(None)
    email: Optional[EmailStr] = Field(None)
    cellphone: Optional[CellphoneStr] = Field(None)
    unit: Optional[UnitStr] = Field(None)
    department: Optional[DepartmentStr] = Field(None)
    title: Optional[TitleStr] = Field(None)
    sample_state: MongoSampleStateOfStaffModel
    working_state: MongoStateOfStaffModel


class MongoInOutModel(BaseModel):
    first_record: Optional[datetime] = Field(None, description="first record in the database")
    last_record: Optional[datetime] = Field(None, description="last record in the database")


class PersonInout(MongoStaffModel, MongoInOutModel):
    model_config = ConfigDict(extra="allow")


class PersonInoutCollection(BaseModel):
    count: int
    values: list[PersonInout]
