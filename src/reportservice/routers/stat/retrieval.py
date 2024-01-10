from typing import List
from datetime import datetime, timezone
from motor.motor_asyncio import AsyncIOMotorCollection, AsyncIOMotorDatabase
from fastapi import APIRouter, Body, Request, HTTPException, status, Depends
import pandas as pd
from ..config.router import get_settings
from .models import StaffCodeStr, DFConst, QueryException
from .queries import pipeline_staffs_inou, pipeline_count


async def get_people_count(
    db: AsyncIOMotorDatabase,
    staff_collection: str,
    bodyfacename_collection: str,
    begin: datetime = "2023-12-27T00:00:00.000+00:00",
    end: datetime = "2023-12-27T23:59:59.999+00:00",
) -> int:
    """count all people in the database"""
    staff_collection: AsyncIOMotorCollection = db[staff_collection]
    count = await staff_collection.distinct("staff_code")
    return len(count)


async def get_has_sample_count(
    db: AsyncIOMotorDatabase,
    staff_collection: str,
    bodyfacename_collection: str,
    begin: datetime = "2023-12-27T00:00:00.000+00:00",
    end: datetime = "2023-12-27T23:59:59.999+00:00",
) -> int:
    raise NotImplementedError


async def get_inout_count(
    db: AsyncIOMotorDatabase,
    staff_collection: str,
    bodyfacename_collection: str,
    begin: datetime = "2023-12-27T00:00:00.000+00:00",
    end: datetime = "2023-12-27T23:59:59.999+00:00",
) -> int:
    if not isinstance(begin, datetime):
        begin = datetime.fromisoformat(begin)
    if not isinstance(end, datetime):
        end = datetime.fromisoformat(end)
    pipeline = pipeline_count(begin, end, 0.63)
    # Execute the pipeline
    bodyfacename_collection: AsyncIOMotorCollection = db[bodyfacename_collection]
    cursor = bodyfacename_collection.aggregate(pipeline)
    result = await cursor.to_list(length=1)

    if not result:
        return 0
    else:
        return result[0]["count"]


async def get_dataframe(
    db: AsyncIOMotorDatabase,
    staff_collection: str,
    bodyfacename_collection: str,
    staffcodes: List[StaffCodeStr],
    begin: datetime = "2023-12-27T00:00:00.000+00:00",
    end: datetime = "2023-12-27T23:59:59.999+00:00",
) -> pd.DataFrame:
    """give a list of staffcode, return a dataframe which contains following columns:
    - staffcode
    - first recognition time
    - last recognition time
    - has_sample

    If a staffcode is not exists in the database, the result will not contains it.

    Please note that the order in result might not be the same as the order of `staffcodes`


    Args:
        collection (AsyncIOMotorCollection): database collection
        staffcodes (List[StaffCodeStr]): just a list of interested staffcode
        begin (datetime): begin of the query window. Defaults to "2023-12-27T00:00:00.000+00:00".
        end (datetime): end of the query window. Defaults to "2023-12-27T23:59:59.999+00:00".

    Raises:
        NotImplementedError: _description_

    Returns:
        pd.DataFrame: if any of arguments is invalid, return an empty dataframe
    """
    if not isinstance(begin, datetime):
        begin = datetime.fromisoformat(begin)
    if not isinstance(end, datetime):
        end = datetime.fromisoformat(end)
    if not isinstance(staffcodes, List):
        df = pd.DataFrame(columns=[DFConst.STAFF, DFConst.FIRST, DFConst.LASTT, DFConst.SAMPL])
        return df

    pipeline = pipeline_staffs_inou(
        staffcodes, begin, end, threshold=0.0, bodyfacename_collection=bodyfacename_collection
    )
    staff_collection: AsyncIOMotorCollection = db[staff_collection]
    cursor = staff_collection.aggregate(pipeline)
    query_result = await cursor.to_list(length=None)
    if len(query_result) == 0:
        df = pd.DataFrame(columns=[DFConst.STAFF, DFConst.FIRST, DFConst.LASTT, DFConst.SAMPL])
        return df
    df = pd.DataFrame(query_result)  # noqa: F841

    if DFConst.STAFF not in df.columns:
        raise QueryException(
            f'in query result, field "{DFConst.STAFF}" not found. Please check the schemas in mongo database'
        )

    if DFConst.FIRST not in df.columns:
        raise QueryException(
            f'in query result, field "{DFConst.FIRST}" not found. Please check the schemas in mongo database'
        )

    if DFConst.LASTT not in df.columns:
        raise QueryException(
            f'in query result, field "{DFConst.LASTT}" not found. Please check the schemas in mongo database'
        )

    if DFConst.SAMPL not in df.columns:
        raise QueryException(
            f'in query result, field "{DFConst.SAMPL}" not found. Please check the schemas in mongo database'
        )

    # TODO: make sure the dataframe has the AppCost.ESTAFF columns
    return df


router = APIRouter()


@router.get("/inout")
async def api_get_inout_count(
    request: Request,
    begin: datetime = "2023-12-27T00:00:00.000+00:00",
    end: datetime = "2023-12-27T23:59:59.999+00:00",
) -> int:
    app_config = await get_settings(request.app.config, request.app.mongodb)
    db = request.app.mongodb

    return await get_inout_count(
        db, app_config.faceiddb.staff_collection, app_config.faceiddb.face_collection, begin, end
    )


@router.get("/people")
async def api_get_people_count(
    request: Request,
    begin: datetime = "2023-12-27T00:00:00.000+00:00",
    end: datetime = "2023-12-27T23:59:59.999+00:00",
) -> int:
    app_config = await get_settings(request.app.config, request.app.mongodb)
    db = request.app.mongodb
    return await get_people_count(
        db, app_config.faceiddb.staff_collection, app_config.faceiddb.face_collection, begin, end
    )


@router.post("/dataframe")
async def api_get_dataframe(
    request: Request,
    staffcodes: List[StaffCodeStr] = Body(...),
    begin: datetime = "2023-12-27T00:00:00.000+00:00",
    end: datetime = "2023-12-27T23:59:59.999+00:00",
) -> str:
    app_config = await get_settings(request.app.config, request.app.mongodb)
    df = await get_dataframe(
        db=request.app.mongodb,
        staff_collection=app_config.faceiddb.staff_collection,
        bodyfacename_collection=app_config.faceiddb.face_collection,
        staffcodes=staffcodes,
        begin=begin,
        end=end,
    )
    return df.to_csv(index=False)
