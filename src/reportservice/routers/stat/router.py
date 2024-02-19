from typing import Annotated, List
from datetime import datetime
from fastapi import APIRouter, Body
from ..common import DepStaffCollection, DepBodyFaceNameCollection, DepLogger
from .retrieval import (
    get_inout_count,
    get_people_count,
    get_people_inout,
    get_has_sample_count,
    get_should_checkinout_count,
)
from .models import QueryParamters, PersonInoutCollection


router = APIRouter()


@router.get("/count_inout")
async def api_get_inout_count(
    bodyfacename_collection: DepBodyFaceNameCollection,
    begin: datetime = "2023-12-27T00:00:00.000+00:00",
    end: datetime = "2023-12-27T23:59:59.999+00:00",
) -> int:
    """Get the count of people represented in a given time range"""
    return await get_inout_count(bodyfacename_collection, begin, end)


@router.get("/count_people")
async def api_get_people_count(staff_collection: DepStaffCollection) -> int:
    """Count all people in the database"""
    return await get_people_count(staff_collection)


@router.get("/count_has_sample")
async def api_get_has_sample_count(staff_collection: DepStaffCollection) -> int:
    """Count the number of people who have face sample in the database"""
    return await get_has_sample_count(staff_collection)


@router.get("/count_should_checkinout")
async def api_get_should_checkinout_count(staff_collection: DepStaffCollection) -> int:
    """should_diemdanh: count the number of people who should be reminded to check in/out today."""
    return await get_should_checkinout_count(staff_collection)


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
