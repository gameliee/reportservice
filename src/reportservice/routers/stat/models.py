"""data models"""
from typing import Annotated, Optional
from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field

StaffCodeStr = Annotated[str, "staff code"]


class QueryException(Exception):
    pass


class PersonInout(BaseModel):
    model_config = ConfigDict(extra="allow")
    staff_code: StaffCodeStr
    full_name: str
    state: str
    first_record: Optional[datetime] = Field(None, alias="first record in the database")
    last_record: Optional[datetime] = Field(None, alias="last record in the database")
