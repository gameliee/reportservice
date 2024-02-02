from typing import Optional, List
from datetime import datetime, timedelta
from pydantic import BaseModel, EmailStr, Field, ConfigDict
from ..stat import PersonInoutCollection
from ..models import ContentModelBase, JinjaStr


class ContentModelCreate(ContentModelBase):
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "name": "example content",
                "description": "just an example content",
                "to": ["example@example.com"],
                "checkin_begin": "2000-01-01 07:00:00",
                "checkin_duration": "PT2H",
                "checkout_begin": "2000-01-01 17:00:00",
                "checkout_duration": "PT2H",
                "subject_template": "please use {{year}}",
                "body_template": "please use {{people_count}}",
                "attach_name_template": "{{year}}{{month}}{{date}}-{{hour}}{{min}}{{sec}}.xlsx",
                "query_parameters": {"units": ["C5"]},
            }
        }
    )


class ContentModelUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    to: Optional[List[EmailStr]] = None
    cc: Optional[List[EmailStr]] = None
    bcc: Optional[List[EmailStr]] = None
    subject_template: Optional[JinjaStr] = None
    body_template: Optional[JinjaStr] = None
    attach: Optional[bool] = None
    checkin_begin: Optional[datetime] = None
    checkin_duration: Optional[timedelta] = None
    checkout_begin: Optional[datetime] = None
    checkout_duration: Optional[timedelta] = None
    attach_name_template: Optional[JinjaStr] = None

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "description": "change the description to this informative one",
            }
        }
    )


class ContentQueryResult(BaseModel):
    query_time: datetime
    people_count: int
    checkin_count: int
    checkout_count: int
    should_checkinout_count: int  # old name is should_diemdanh
    total_count: int
    people_inout: PersonInoutCollection


class ContentModelRendered(BaseModel):
    to: str
    cc: str
    bcc: str
    subject: str
    body: str
    attach: Optional[str] = Field(None, description="excel file in base64 string")
    attach_name: Optional[str] = Field(None, description="name of the attached excel file")


class ExcelColumn:
    ESTAFF = "mã nhân viên"
    EFIRST = "ghi nhận lần đầu"
    ELASTT = "ghi nhận lần cuối"
    ESAMPL = "trạng thái mẫu"


class ExcelInvalidException(Exception):
    pass
