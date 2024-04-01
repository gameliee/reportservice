from typing import List, Any
from datetime import datetime
import logging
from motor.motor_asyncio import AsyncIOMotorCollection
from .models import QueryParamters, PersonInoutCollection, PersonInout, PersonRecord, PersonRecordCollection
from .queries import (
    pipeline_count,
    query_find_staff,
    query_find_staff_inout,
    pipeline_count_shoulddiemdanh,
    pipeline_count_has_sample,
    pipeline_get_record_by_id,
    condition_count_record_by_id,
)


async def get_people_count(staff_collection: AsyncIOMotorCollection) -> int:
    """count all people in the database"""
    count = await staff_collection.distinct("staff_code")
    return len(count)


async def get_has_sample_count(staff_collection: AsyncIOMotorCollection) -> int:
    """count the number of people who have face sample in the database"""
    cursor = staff_collection.aggregate(pipeline_count_has_sample())
    result = await cursor.to_list(length=1)
    if result:
        return result[0]["count"]
    else:
        return 0


async def get_should_checkinout_count(staff_collection: AsyncIOMotorCollection) -> int:
    """should_diemdanh: count the number of people who should be reminded to check in/out today."""
    cursor = staff_collection.aggregate(pipeline_count_shoulddiemdanh())
    result = await cursor.to_list(length=1)
    if result:
        return result[0]["count"]
    else:
        return 0


async def get_inout_count(
    bodyfacename_collection: AsyncIOMotorCollection,
    begin: datetime = "2023-12-27T00:00:00.000+00:00",
    end: datetime = "2023-12-27T23:59:59.999+00:00",
) -> int:
    """Get the count of people represented in a given time range"""
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
    logger: logging.Logger | None = None,
) -> PersonInoutCollection:
    """
    query the first and last recognition time of each staffcode in the database
    Please note that the order in result might not be the same as the order of `staffcodes`.
    The length of result should be the same as the length of `staffcodes`.
    """
    if logger is None:
        logger = logging.getLogger()
    if not isinstance(begin, datetime):
        begin = datetime.fromisoformat(begin)
    if not isinstance(end, datetime):
        end = datetime.fromisoformat(end)

    if query_params.is_empty():
        return PersonInoutCollection(count=0, values=[])

    # NOTE: need to use two stage query here because the $lookup stage can not use index
    # might be fixed in the future

    # first stage: find all the staffs
    stage1 = query_find_staff(query_params)
    logger.debug(f"running in-out pipeline stage1: {stage1}")
    cursor1 = staff_collection.aggregate(stage1)
    final_result: List[PersonInout] = []
    async for document in cursor1:
        staff = PersonInout.model_validate(document)
        final_result.append(staff)

    logger.debug(f"running in-out pipeline stage1 result: {final_result}")

    # second stage: find in-out information related to the first stage
    staffcodes = [staff.staff_code for staff in final_result]
    stage2 = query_find_staff_inout(staffcodes, begin, end, 0.63, False)
    logger.debug(f"running in-out pipeline stage2: {stage2}")
    cursor2 = bodyfacename_collection.aggregate(stage2)

    # now merge the results of stage1 and stage2 together
    _stage2_result: List[Any] = []
    async for document in cursor2:
        _stage2_result.append(document)
        staffcode = document["staff_code"]
        for staff in final_result:
            if staff.staff_code == staffcode:
                staff.first_record = document["firstDocument"]
                staff.last_record = document["lastDocument"]
                break

    logger.debug(f"running in-out pipeline stage2 result: {_stage2_result}")

    return PersonInoutCollection(count=len(final_result), values=final_result)


async def get_person_count_by_id(
    bodyfacename_collection: AsyncIOMotorCollection,
    staff_code: str | None = None,
    begin: datetime = "2023-12-27T00:00:00.000+00:00",
    end: datetime = "2023-12-27T23:59:59.999+00:00",
    face_reg_score_threshold: float = 0.63,
    has_mask: bool = False,
    logger: logging.Logger | None = None,
) -> int:
    if logger is None:
        logger = logging.getLogger()
    if not isinstance(begin, datetime):
        begin = datetime.fromisoformat(begin)
    if not isinstance(end, datetime):
        end = datetime.fromisoformat(end)

    condition = condition_count_record_by_id(begin, end, staff_code, face_reg_score_threshold, has_mask)

    count = await bodyfacename_collection.count_documents(condition)
    return count


async def get_person_record_by_id(
    bodyfacename_collection: AsyncIOMotorCollection,
    staff_code: str | None = None,
    begin: datetime = "2023-12-27T00:00:00.000+00:00",
    end: datetime = "2023-12-27T23:59:59.999+00:00",
    face_reg_score_threshold: float = 0.63,
    has_mask: bool = False,
    offset: int = 0,
    limit: int = 10,
    logger: logging.Logger | None = None,
) -> PersonRecordCollection:
    if logger is None:
        logger = logging.getLogger()
    if not isinstance(begin, datetime):
        begin = datetime.fromisoformat(begin)
    if not isinstance(end, datetime):
        end = datetime.fromisoformat(end)

    count = await get_person_count_by_id(
        bodyfacename_collection, staff_code, begin, end, face_reg_score_threshold, has_mask, logger
    )
    pipeline = pipeline_get_record_by_id(begin, end, staff_code, face_reg_score_threshold, has_mask, offset, limit)
    logger.debug(f"running get_person_record_by_id pipeline: {pipeline}")
    cursor = bodyfacename_collection.aggregate(pipeline)
    final_result: List[PersonRecord] = []
    async for document in cursor:
        record = PersonRecord.model_validate(document)
        final_result.append(record)

    return PersonRecordCollection(count=count, values=final_result)
