from typing import Optional
from pydantic import Field, EmailStr, ConfigDict, PrivateAttr
from pydantic_settings import BaseSettings

FIXID = "dontchangeme"


class FaceIDDBSettingsModelUpdate(BaseSettings):
    staff_collection: Optional[str] = None
    face_collection: Optional[str] = None


class FaceIDDBSettingsModel(BaseSettings):
    staff_collection: str
    face_collection: str
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "staff_collection": "staffs",
                "face_collection": "BodyFaceName",
            }
        }
    )

    def update(self, u: FaceIDDBSettingsModelUpdate):
        for k, v in u.model_dump(exclude_none=True).items():
            setattr(self, k, v)


class SmtpSettingsModelUpdate(BaseSettings):
    enable: Optional[bool] = None
    username: Optional[str] = None
    account: Optional[EmailStr] = None
    password: Optional[str] = None
    server: Optional[str] = None
    port: Optional[int] = None
    useSSL: Optional[bool] = None


class SmtpSettingsModel(BaseSettings):
    enable: bool = False
    username: str
    account: EmailStr
    password: str
    server: str
    port: int
    useSSL: bool
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "enable": "true",
                "username": "testuser",
                "account": "testnv@example.com",
                "password": "",
                "server": "localhost",
                "port": 1026,
                "useSSL": False,
            }
        }
    )

    def update(self, u: SmtpSettingsModelUpdate):
        for k, v in u.model_dump(exclude_none=True).items():
            setattr(self, k, v)


class AppSettingsModelUpdate(BaseSettings):
    faceiddb: Optional[FaceIDDBSettingsModelUpdate] = None
    smtp: Optional[SmtpSettingsModelUpdate] = None
    model_config = ConfigDict(populate_by_name=True)

    def to_flatten(self) -> dict:
        """to flatten dict, suitable to add into pymongo"""
        ret = {}
        if self.faceiddb is not None:
            for k, v in self.faceiddb.model_dump(exclude_none=True).items():
                ret[f"faceiddb.{k}"] = v
        if self.smtp is not None:
            for k, v in self.smtp.model_dump(exclude_none=True).items():
                ret[f"smtp.{k}"] = v
        return ret


class AppSettingsModel(BaseSettings):
    _id: str = PrivateAttr(FIXID)
    faceiddb: FaceIDDBSettingsModel
    smtp: SmtpSettingsModel
    model_config = ConfigDict(populate_by_name=True)

    def update(self, u: AppSettingsModelUpdate):
        if u.faceiddb is not None:
            self.faceiddb.update(u.faceiddb)
        if u.smtp is not None:
            self.smtp.update(u.smtp)
