from typing import List
from datetime import datetime
from motor.motor_asyncio import AsyncIOMotorCollection
from .models import QueryParamters, PersonInoutCollection, PersonInout
from .queries import pipeline_staffs_inou, pipeline_count


async def get_people_count(
    staff_collection: AsyncIOMotorCollection,
    begin: datetime = "2023-12-27T00:00:00.000+00:00",
    end: datetime = "2023-12-27T23:59:59.999+00:00",
) -> int:
    """count all people in the database"""
    count = await staff_collection.distinct("staff_code")
    return len(count)


async def get_has_sample_count(
    staff_collection: AsyncIOMotorCollection,
    bodyfacename_collection: AsyncIOMotorCollection,
    begin: datetime = "2023-12-27T00:00:00.000+00:00",
    end: datetime = "2023-12-27T23:59:59.999+00:00",
) -> int:
    raise NotImplementedError


async def get_inout_count(
    bodyfacename_collection: AsyncIOMotorCollection,
    begin: datetime = "2023-12-27T00:00:00.000+00:00",
    end: datetime = "2023-12-27T23:59:59.999+00:00",
) -> int:
    if not isinstance(begin, datetime):
        begin = datetime.fromisoformat(begin)
    if not isinstance(end, datetime):
        end = datetime.fromisoformat(end)
    pipeline = pipeline_count(begin, end, 0.63)
    # Execute the pipeline
    cursor = bodyfacename_collection.aggregate(pipeline)
    result = await cursor.to_list(length=1)

    if not result:
        return 0
    else:
        return result[0]["count"]


async def get_people_inout(
    staff_collection: AsyncIOMotorCollection,
    bodyfacename_collection: AsyncIOMotorCollection,
    query_params: QueryParamters,
    begin: datetime = "2023-12-27T00:00:00.000+00:00",
    end: datetime = "2023-12-27T23:59:59.999+00:00",
) -> PersonInoutCollection:
    """
    query the first and last recognition time of each staffcode in the database
    Please note that the order in result might not be the same as the order of `staffcodes`.
    The length of result should be the same as the length of `staffcodes`.
    """
    if not isinstance(begin, datetime):
        begin = datetime.fromisoformat(begin)
    if not isinstance(end, datetime):
        end = datetime.fromisoformat(end)

    if query_params.is_empty():
        return PersonInoutCollection(count=0, values=[])

    pipeline = pipeline_staffs_inou(
        query_params,
        begin,
        end,
        threshold=0.0,
        bodyfacename_collection_name=bodyfacename_collection.name,
    )
    cursor = staff_collection.aggregate(pipeline)

    ret: List[PersonInout] = []
    async for document in cursor:
        personinout = PersonInout.model_validate(document)
        ret.append(personinout)

    return PersonInoutCollection(count=len(ret), values=ret)
