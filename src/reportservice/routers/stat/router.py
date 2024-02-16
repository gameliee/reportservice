from typing import Annotated, List
from datetime import datetime
from fastapi import APIRouter, Body
from ..common import DepStaffCollection, DepBodyFaceNameCollection, DepLogger
from .retrieval import get_inout_count, get_people_count, get_people_inout
from .models import QueryParamters, PersonInoutCollection


router = APIRouter()


@router.get("/inout")
async def api_get_inout_count(
    bodyfacename_collection: DepBodyFaceNameCollection,
    begin: datetime = "2023-12-27T00:00:00.000+00:00",
    end: datetime = "2023-12-27T23:59:59.999+00:00",
) -> int:
    """Get the count of people represented in a given time range"""
    return await get_inout_count(bodyfacename_collection, begin, end)


@router.get("/people")
async def api_get_people_count(
    staff_collection: DepStaffCollection,
    begin: datetime = "2023-12-27T00:00:00.000+00:00",
    end: datetime = "2023-12-27T23:59:59.999+00:00",
) -> int:
    """Count all people in the database"""
    return await get_people_count(staff_collection, begin, end)


@router.post("/people_inout", response_model=PersonInoutCollection)
async def api_get_people_inout(
    staff_collection: DepStaffCollection,
    bodyfacename_collection: DepBodyFaceNameCollection,
    logger: DepLogger,
    query_params: QueryParamters = Body(...),
    begin: datetime = "2023-12-27T00:00:00.000+00:00",
    end: datetime = "2023-12-27T23:59:59.999+00:00",
) -> PersonInoutCollection:
    """Query the first and last recognition time of each staffcode in the database"""
    peopleinout = await get_people_inout(
        staff_collection, bodyfacename_collection, query_params=query_params, begin=begin, end=end, logger=logger
    )

    return peopleinout
