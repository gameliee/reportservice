from fastapi import APIRouter, Body, HTTPException, status
from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder
from ..common import AppConfigModel, AppConfigModelUpdate
from ..common import DepAppConfig, DepConfigCollection
from ..common import AsyncEmailSpammer

router = APIRouter()


async def validate_config(config: AppConfigModel) -> bool:
    # TODO: validate the collection names
    try:
        # construct email connection here
        if config.smtp.enable:
            spammer = AsyncEmailSpammer(
                config.smtp.username,
                config.smtp.account,
                config.smtp.password,
                config.smtp.server,
                config.smtp.port,
                useSSL=config.smtp.useSSL,
            )
            await spammer.connect()
    except Exception as e:
        raise HTTPException(
            status_code=422, detail=f"Email settings did not work: {e} with settings {config.smtp}"
        ) from e
    return True


@router.post(
    "/", status_code=201, response_model=AppConfigModel, responses={409: {"description": "Already have settings"}}
)
async def create_config(collection: DepConfigCollection, config: AppConfigModel = Body(...)):
    latest = await collection.find_one()
    if latest is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="already have settings, please use PUT or DELETE"
        )

    await validate_config(config)
    config_json = jsonable_encoder(config)
    new_setting = await collection.insert_one(config_json)
    created_setting = await collection.find_one({"_id": new_setting.inserted_id})
    # created_setting.pop("_id")
    return JSONResponse(status_code=status.HTTP_201_CREATED, content=created_setting)


responses = {404: {"description": "No config found"}}


@router.get("/", response_model=AppConfigModel, responses=responses)
async def api_get_config(_config: DepAppConfig):
    """Get Config"""
    return _config.model_dump()


@router.put("/", response_model=AppConfigModel, responses=responses)
async def update_config(
    collection: DepConfigCollection, oldconfig: DepAppConfig, config: AppConfigModelUpdate = Body(...)
):
    id = oldconfig.id
    latest = oldconfig
    latest.update(config)
    await validate_config(AppConfigModel.model_validate(latest))

    # turn to something like "smtp.username": "hola"
    fields = config.to_flatten()
    if len(fields) >= 1:
        update_result = await collection.update_one({"_id": id}, {"$set": fields})
        if update_result.modified_count == 1:
            if (updated_settings := await collection.find_one({"_id": id})) is not None:
                updated_settings.pop("_id")
                return updated_settings

    if (existing_settings := await collection.find_one({"_id": id})) is not None:
        existing_settings.pop("_id")
        return existing_settings

    raise HTTPException(status_code=404, detail="No config found")
