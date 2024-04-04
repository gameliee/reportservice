import uuid
from typing import Optional, List, Annotated
from datetime import datetime, timedelta
from fastapi import HTTPException, status
from pydantic import BaseModel, EmailStr, Field, ConfigDict
from pydantic.functional_validators import AfterValidator
from jinja2 import Environment, BaseLoader, Template
from jinja2.exceptions import TemplateSyntaxError
from ..stat import PersonInoutCollection
from ..models import QueryParamters, ContentId


def validate_jinja(v: str) -> str:
    try:
        Environment(loader=BaseLoader).from_string(v)
    except TemplateSyntaxError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Jinja string error {e}") from e
    return v


JinjaStr = Annotated[str, AfterValidator(validate_jinja)]
ExcelAsStr = Annotated[str, "excel file in base64 string"]


class ContentModelBase(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    id: ContentId = Field(default_factory=lambda: str(uuid.uuid4()), alias="_id")
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
    to: Optional[List[EmailStr]] = Field(None, min_length=1)
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
    has_sample_count: int
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
