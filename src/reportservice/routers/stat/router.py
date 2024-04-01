from datetime import datetime
from typing import Optional
from pydantic import AwareDatetime
from fastapi import APIRouter, Body
from ..common import DepStaffCollection, DepBodyFaceNameCollection, DepLogger
from .retrieval import (
    get_inout_count,
    get_people_count,
    get_people_inout,
    get_has_sample_count,
    get_should_checkinout_count,
    get_person_record_by_id,
)
from .models import QueryParamters, PersonInoutCollection, PersonRecordCollection, StaffCodeStr


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


@router.get("/person_record")
async def api_get_person_record_by_id(
    bodyfacename_collection: DepBodyFaceNameCollection,
    logger: DepLogger,
    staff_id: StaffCodeStr | None = None,
    begin: Optional[AwareDatetime] = None,
    end: Optional[AwareDatetime] = None,
    face_reg_score_threshold: float = 0.63,
    has_mask: bool = False,
    offset: int = 0,
    limit: int = 10,
) -> PersonRecordCollection:
    """Get the recognition record of a person by staff_code
    if bot begin and end are not provided, the function will return the records for today (+07 timezone)
    """
    if begin is None and end is None:
        begin = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0).astimezone()
        end = datetime.now().replace(hour=23, minute=59, second=59, microsecond=999).astimezone()

    if end is None:
        end = datetime.now().astimezone()

    return await get_person_record_by_id(
        bodyfacename_collection=bodyfacename_collection,
        staff_code=staff_id,
        begin=begin,
        end=end,
        face_reg_score_threshold=face_reg_score_threshold,
        has_mask=has_mask,
        offset=offset,
        limit=limit,
        logger=logger,
    )
