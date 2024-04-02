"""data models"""

from enum import Enum
from bson import json_util
import json
from typing import Annotated, Optional
from datetime import datetime, timezone, date
from pydantic import BaseModel, ConfigDict, Field, AnyHttpUrl, model_validator
from pydantic.functional_validators import BeforeValidator

__all__ = [
    "QueryParamters",
    "QueryException",
    "PersonInout",
    "PersonInoutCollection",
    "MongoSampleStateOfStaffModel",
    "MongoStateOfStaffModel",
]

StaffCodeStr = Annotated[str, "staff code"]
FullNameStr = Annotated[str, "full name"]
UnitStr = Annotated[str, "unit name"]
DepartmentStr = Annotated[str, "department name"]
TitleStr = Annotated[str, "title name"]
EmailStr = Annotated[str, "email address"]
CellphoneStr = Annotated[str, "cellphone number"]
CameraIdStr = Annotated[str, "camera id"]


def validate_query(query_string):
    if isinstance(query_string, dict):
        return query_string
    # Attempt to parse the query string into a Python dictionary
    query_string = json.loads(query_string, object_hook=json_util.object_hook)
    return query_string


MongoQueryStr = Annotated[dict, "mongo query string", BeforeValidator(validate_query)]


class QueryParamters(BaseModel):
    """These parameters should be OR together"""

    staffcodes: list[StaffCodeStr] = []
    fullnames: list[FullNameStr] = []
    units: list[UnitStr] = []
    departments: list[DepartmentStr] = []
    titles: list[TitleStr] = []
    emails: list[EmailStr] = []
    cellphones: list[CellphoneStr] = []
    custom_query: MongoQueryStr = {"$eq": [1, 0]}

    def is_empty(self):
        return (
            len(self.staffcodes)
            + len(self.fullnames)
            + len(self.units)
            + len(self.departments)
            + len(self.titles)
            + len(self.emails)
            + len(self.cellphones)
            == 0
        ) and self.custom_query == {"$eq": [1, 0]}


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


class PersonRecord(BaseModel):
    staff_id: StaffCodeStr
    full_name: Optional[FullNameStr] = None
    camera_id: CameraIdStr
    image_time: datetime
    face_reg_score: float
    img_link: Optional[AnyHttpUrl] = None

    @model_validator(mode="after")
    def convert_image_time(self) -> "PersonRecord":
        if self.image_time.tzinfo is None:
            self.image_time = self.image_time.replace(tzinfo=timezone.utc)
        return self


class PersonRecordCollection(BaseModel):
    count: int
    values: list[PersonRecord]


class ByDateCam(BaseModel):
    """The store model for the count of person in a camera in a day."""

    date: date
    camera_id: CameraIdStr
    count: int


class ByDateCamCollection(BaseModel):
    count: int
    values: list[ByDateCam]
