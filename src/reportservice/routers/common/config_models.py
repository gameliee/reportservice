from typing import Optional
from pydantic import Field, EmailStr, ConfigDict, PrivateAttr
from pydantic_settings import BaseSettings

FIXID = "dontchangeme"


class FaceIDDBConfigModelUpdate(BaseSettings):
    database: Optional[str] = None
    staff_collection: Optional[str] = None
    face_collection: Optional[str] = None


class FaceIDDBConfigModel(BaseSettings):
    database: str
    staff_collection: str
    face_collection: str
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "database": "FaceID",
                "staff_collection": "staffs",
                "face_collection": "BodyFaceName",
            }
        }
    )

    def update(self, u: FaceIDDBConfigModelUpdate):
        for k, v in u.model_dump(exclude_none=True).items():
            setattr(self, k, v)


class SmtpConfigModelUpdate(BaseSettings):
    enable: Optional[bool] = None
    username: Optional[str] = None
    account: Optional[EmailStr] = None
    password: Optional[str] = None
    server: Optional[str] = None
    port: Optional[int] = None
    useSSL: Optional[bool] = None


class SmtpConfigsModel(BaseSettings):
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

    def update(self, u: SmtpConfigModelUpdate):
        for k, v in u.model_dump(exclude_none=True).items():
            setattr(self, k, v)


class AppConfigModelUpdate(BaseSettings):
    faceiddb: Optional[FaceIDDBConfigModelUpdate] = None
    smtp: Optional[SmtpConfigModelUpdate] = None
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


class AppConfigModel(BaseSettings):
    id: str = Field(FIXID, alias="_id", frozen=True, description="the config id in the database, never change me")
    faceiddb: FaceIDDBConfigModel
    smtp: SmtpConfigsModel
    model_config = ConfigDict(populate_by_name=True)

    def update(self, u: AppConfigModelUpdate):
        if u.faceiddb is not None:
            self.faceiddb.update(u.faceiddb)
        if u.smtp is not None:
            self.smtp.update(u.smtp)
