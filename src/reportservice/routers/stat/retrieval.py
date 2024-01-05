from typing import List
from datetime import datetime, timezone
from motor.motor_asyncio import AsyncIOMotorCollection
from fastapi import APIRouter, Body, Request, HTTPException, status, Depends
import pandas as pd
from .models import StaffCodeStr


async def get_people_count(
    collecttion: AsyncIOMotorCollection,
    begin: datetime = "2023-12-27T00:00:00.000+00:00",
    end: datetime = "2023-12-27T23:59:59.999+00:00",
) -> int:
    raise NotImplementedError


async def get_inout_count(
    collecttion: AsyncIOMotorCollection,
    begin: datetime = "2023-12-27T00:00:00.000+00:00",
    end: datetime = "2023-12-27T23:59:59.999+00:00",
) -> int:
    if not isinstance(begin, datetime):
        begin = datetime.fromisoformat(begin)
    if not isinstance(end, datetime):
        end = datetime.fromisoformat(end)
    pipeline = [
        {
            "$match": {
                "image_time": {
                    "$gte": begin,
                    "$lte": end,
                },
                "face_reg_score": {"$gte": 0.63},
                "has_mask": False,
            }
        },
        {"$group": {"_id": "$staff_id"}},
        {"$group": {"_id": None, "count": {"$sum": 1}}},
        {"$project": {"_id": 0, "count": 1}},
    ]
    # Execute the pipeline
    cursor = collecttion.aggregate(pipeline)
    result = await cursor.to_list(length=1)

    print(pipeline)
    print(result)

    if not result:
        return 0
    else:
        return result[0]["count"]


async def get_dataframe(
    collection: AsyncIOMotorCollection,
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

    pipeline = [
        {
            "$match": {
                "image_time": {"$gte": begin, "$lte": end},
                "face_reg_score": {"$gte": 0.63},
                "has_mask": False,
                "staff_id": {"$in": staffcodes},
            }
        },
        {"$project": {"staff_id": 1, "image_time": 1}},
        {"$sort": {"image_time": 1}},
        {"$group": {"_id": "$staff_id", "first": {"$first": "$image_time"}, "last": {"$last": "$image_time"}}},
    ]

    cursor = collection.aggregate(pipeline)
    query_result = await cursor.to_list(length=None)
    df = pd.DataFrame(query_result)  # noqa: F841

    raise NotImplementedError


router = APIRouter()


@router.get("/")
async def api_get_inout_count(
    request: Request,
    begin: datetime = "2023-12-27T00:00:00.000+00:00",
    end: datetime = "2023-12-27T23:59:59.999+00:00",
) -> int:
    return await get_inout_count(request.app.collection, begin, end)
