from datetime import datetime
from typing import List, AsyncIterable
from contextlib import asynccontextmanager
from fastapi import APIRouter, Body, Request, HTTPException, status, Depends
from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder
from motor.motor_asyncio import AsyncIOMotorDatabase
from .models import AppSettingsModel, AppSettingsModelUpdate
from .email_spammer import EmailSpammer

router = APIRouter()


async def validate_settings(setting: AppSettingsModel) -> bool:
    # TODO: validate the collection names
    try:
        # construct email connection here
        if setting.smtp.enable:
            EmailSpammer(
                setting.smtp.username,
                setting.smtp.account,
                setting.smtp.password,
                setting.smtp.server,
                setting.smtp.port,
                useSSL=setting.smtp.useSSL,
            )
    except Exception as e:
        raise HTTPException(status_code=422, detail=f"Email settings did not work: {e} with settings {setting.smtp}")
    return True


@router.post("/", response_description="Create Settings", response_model=AppSettingsModel)
async def create_settings(request: Request, setting: AppSettingsModel = Body(...)):
    COLNAME = request.app.config.DB_COLLECTION_SETTINGS
    latest = await request.app.mongodb[COLNAME].find_one()
    if latest is not None:
        raise HTTPException(status_code=303, detail="already have settings, please use PUT or DELETE")

    await validate_settings(setting)
    collection = request.app.mongodb[COLNAME]
    setting = jsonable_encoder(setting)
    new_setting = await collection.insert_one(setting)
    created_setting = await collection.find_one({"_id": new_setting.inserted_id})
    created_setting.pop("_id")
    return JSONResponse(status_code=status.HTTP_201_CREATED, content=created_setting)


async def get_settings(config: AppSettingsModel, db: AsyncIOMotorDatabase) -> AppSettingsModel:
    collection = db[config.DB_COLLECTION_SETTINGS]
    latest = await collection.find_one()
    if not latest:
        raise HTTPException(status_code=404, detail="No settings found")
    latest.pop("_id")
    return AppSettingsModel.model_validate(latest)


@router.get("/", response_description="Get Settings", response_model=AppSettingsModel)
async def api_get_settings(request: Request):
    latest = await get_settings(request.app.config, request.app.mongodb)
    return latest.model_dump()


@router.put("/", response_description="Update settings", response_model=AppSettingsModel)
async def update_settings(request: Request, setting: AppSettingsModelUpdate = Body(...)):
    COLNAME = request.app.config.DB_COLLECTION_SETTINGS
    latest = await request.app.mongodb[COLNAME].find_one()
    if not latest:
        raise HTTPException(status_code=404, detail="No settings found")
    id = latest.pop("_id")
    latest = AppSettingsModel.model_validate(latest)
    latest.update(setting)

    await validate_settings(AppSettingsModel.model_validate(latest))

    # turn to something like "smtp.username": "hola"
    fields = setting.to_flatten()

    collection = request.app.mongodb[COLNAME]
    if len(fields) >= 1:
        update_result = await collection.update_one({"_id": id}, {"$set": fields})
        if update_result.modified_count == 1:
            if (updated_settings := await collection.find_one({"_id": id})) is not None:
                updated_settings.pop("_id")
                return updated_settings

    if (existing_settings := await collection.find_one({"_id": id})) is not None:
        existing_settings.pop("_id")
        return existing_settings

    raise HTTPException(status_code=404, detail="No settings found")


@router.delete("/", response_description="Delete settings")
async def delete_settings(request: Request):
    COLNAME = request.app.config.DB_COLLECTION_SETTINGS
    settings = await request.app.mongodb[COLNAME].find_one()
    if not settings:
        raise HTTPException(status_code=404, detail="No settings found")

    id = settings.pop("_id")
    settings = AppSettingsModel.model_validate(settings)

    delete_result = await request.app.mongodb[COLNAME].delete_one({"_id": id})

    if delete_result.deleted_count == 1:
        return JSONResponse(status_code=status.HTTP_200_OK, content="Deleted")

    raise HTTPException(status_code=404, detail="Nothing to delete")


@asynccontextmanager
async def get_spammer(request: Request):
    settings = await get_settings(request)
    settings = AppSettingsModel.model_validate(settings)
    smtpsettings = settings.smtp

    if not smtpsettings.enable:
        yield None
    else:
        spammer = EmailSpammer(
            smtpsettings.username,
            smtpsettings.account,
            smtpsettings.password,
            smtpsettings.server,
            smtpsettings.port,
            useSSL=smtpsettings.useSSL,
        )

        yield spammer
