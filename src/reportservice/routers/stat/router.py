from typing import Annotated, List
from datetime import datetime
from fastapi import APIRouter, Depends, Body
from motor.motor_asyncio import AsyncIOMotorCollection
from ..common import DepAppConfig, DepMongoCLient
from ..common import DepStaffCollection, DepBodyFaceNameCollection
from .retrieval import get_inout_count, get_people_count, get_people_inout
from .models import StaffCodeStr


router = APIRouter()


@router.get("/inout")
async def api_get_inout_count(
    bodyfacename_collection: DepBodyFaceNameCollection,
    begin: datetime = "2023-12-27T00:00:00.000+00:00",
    end: datetime = "2023-12-27T23:59:59.999+00:00",
) -> int:
    return await get_inout_count(bodyfacename_collection, begin, end)


@router.get("/people")
async def api_get_people_count(
    staff_collection: DepStaffCollection,
    begin: datetime = "2023-12-27T00:00:00.000+00:00",
    end: datetime = "2023-12-27T23:59:59.999+00:00",
) -> int:
    return await get_people_count(staff_collection, begin, end)


@router.post("/people_inout")
async def api_get_people_inout(
    staff_collection: DepStaffCollection,
    bodyfacename_collection: DepBodyFaceNameCollection,
    staffcodes: List[StaffCodeStr] = Body(...),
    begin: datetime = "2023-12-27T00:00:00.000+00:00",
    end: datetime = "2023-12-27T23:59:59.999+00:00",
) -> str:
    peopleinout = await get_people_inout(
        staff_collection,
        bodyfacename_collection,
        staffcodes=staffcodes,
        begin=begin,
        end=end,
    )
    return str(peopleinout)
