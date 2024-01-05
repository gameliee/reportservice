from datetime import datetime, timezone
from motor.motor_asyncio import AsyncIOMotorCollection
from fastapi import APIRouter, Body, Request, HTTPException, status, Depends


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


router = APIRouter()


@router.get("/")
async def api_get_inout_count(
    request: Request,
    begin: datetime = "2023-12-27T00:00:00.000+00:00",
    end: datetime = "2023-12-27T23:59:59.999+00:00",
) -> int:
    return await get_inout_count(request.app.collection, begin, end)
