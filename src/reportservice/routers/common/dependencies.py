from logging import Logger
from typing import Annotated, Callable
from fastapi import Request, Depends, HTTPException
from motor.motor_asyncio import AsyncIOMotorDatabase, AsyncIOMotorClient, AsyncIOMotorCollection
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from .config_models import AppConfigModel
from .async_email_spammer import AsyncEmailSpammer
from ...settings import AppSettingsModel

__all__ = [
    "DepAppSettings",
    "DepMongoClient",
    "DepSCheduler",
    "DepConfigCollection",
    "DepContentCollection",
    "DepTaskCollection",
    "DepLogCollection",
    "DepAppConfig",
    "DepBodyFaceNameCollection",
    "DepStaffCollection",
    "DepLogger",
    "DepEmailSpammer",
]


async def get_app_settings(request: Request) -> AppSettingsModel:
    return request.app.settings


DepAppSettings = Annotated[AppSettingsModel, Depends(get_app_settings)]


async def get_database_client(request: Request) -> AsyncIOMotorClient:
    return request.app.mongodb_client


DepMongoClient = Annotated[AsyncIOMotorClient, Depends(get_database_client)]


async def get_scheduler(request: Request) -> AsyncIOScheduler:
    return request.app.scheduler


DepSCheduler = Annotated[AsyncIOScheduler, Depends(get_scheduler)]


async def get_config_collection(settings: DepAppSettings, mongodb_client: DepMongoClient) -> AsyncIOMotorCollection:
    db: AsyncIOMotorDatabase = mongodb_client[settings.DB_REPORT_NAME]
    collection = db[settings.DB_COLLECTION_CONFIG]
    return collection


DepConfigCollection = Annotated[AsyncIOMotorCollection, Depends(get_config_collection)]


async def get_log_collection(settings: DepAppSettings, mongodb_client: DepMongoClient) -> AsyncIOMotorCollection:
    db: AsyncIOMotorDatabase = mongodb_client[settings.DB_REPORT_NAME]
    collection = db[settings.DB_COLLECTION_LOG]
    return collection


DepLogCollection = Annotated[AsyncIOMotorCollection, Depends(get_log_collection)]


async def get_config(collection: DepConfigCollection) -> AppConfigModel:
    latest = await collection.find_one()
    if not latest:
        raise HTTPException(status_code=404, detail="No settings found")
    latest.pop("_id")
    return AppConfigModel.model_validate(latest)


DepAppConfig = Annotated[AppConfigModel, Depends(get_config)]


async def get_content_collection(settings: DepAppSettings, mongodb_client: DepMongoClient) -> AsyncIOMotorCollection:
    db: AsyncIOMotorDatabase = mongodb_client[settings.DB_REPORT_NAME]
    collection = db[settings.DB_COLLECTION_CONTENT]
    return collection


async def get_task_collection(settings: DepAppSettings, mongodb_client: DepMongoClient) -> AsyncIOMotorCollection:
    db: AsyncIOMotorDatabase = mongodb_client[settings.DB_REPORT_NAME]
    collection = db[settings.DB_COLLECTION_TASK]
    return collection


DepContentCollection = Annotated[AsyncIOMotorCollection, Depends(get_content_collection)]
DepTaskCollection = Annotated[AsyncIOMotorCollection, Depends(get_task_collection)]


async def get_faceid_BodyFaceName_collection(
    app_config: DepAppConfig, mongo_client: DepMongoClient
) -> AsyncIOMotorCollection:
    colname = app_config.faceiddb.face_collection
    db = mongo_client[app_config.faceiddb.database]
    return db[colname]


DepBodyFaceNameCollection = Annotated[AsyncIOMotorCollection, Depends(get_faceid_BodyFaceName_collection)]


async def get_faceid_staff_collection(
    app_config: DepAppConfig, mongo_client: DepMongoClient
) -> AsyncIOMotorCollection:
    colname = app_config.faceiddb.staff_collection
    db = mongo_client[app_config.faceiddb.database]
    return db[colname]


DepStaffCollection = Annotated[AsyncIOMotorCollection, Depends(get_faceid_staff_collection)]


async def get_logger(request: Request) -> Logger:
    return request.app.logger


DepLogger = Annotated[Logger, Depends(get_logger)]


async def get_spammer(app_config: DepAppConfig) -> Callable[[], AsyncEmailSpammer] | None:
    smtpconfig = app_config.smtp

    if not smtpconfig.enable:
        yield None
    else:
        # NOTE: do not return spammer directly because it will have to be send "nope" from time to time to keep it alive
        def create_spammer():
            return AsyncEmailSpammer(
                smtpconfig.username,
                smtpconfig.account,
                smtpconfig.password,
                smtpconfig.server,
                smtpconfig.port,
                useSSL=smtpconfig.useSSL,
            )

        yield create_spammer


DepEmailSpammer = Annotated[Callable[[], AsyncEmailSpammer] | None, Depends(get_spammer)]
