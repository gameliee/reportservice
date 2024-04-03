import json
import pytest
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorCollection, AsyncIOMotorDatabase
from ..retrieval import (
    get_people_count,
    get_inout_count,
    get_people_inout,
    get_has_sample_count,
    get_should_checkinout_count,
    get_person_count_by_id,
    get_person_record_by_id,
    get_record_count_by_date_cam,
)
from ..queries import query_find_staff
from ..models import PersonInout, PersonInoutCollection, QueryParamters
from ...common import AppConfigModel
from ...common.conftest import appconfig


@pytest.fixture
def fixture_faceiddb(testsettings, collectionconfig) -> AsyncIOMotorDatabase:
    mongodb_client = AsyncIOMotorClient(testsettings.DB_URL, uuidRepresentation="standard")
    faceid_database_name = collectionconfig["database"]
    mongodb: AsyncIOMotorDatabase = mongodb_client[faceid_database_name]
    return mongodb


@pytest.fixture
def fixture_bodyfacename_collection(
    fixture_faceiddb,
    appconfig: AppConfigModel,  # noqa: F811
) -> AsyncIOMotorCollection:
    return fixture_faceiddb[appconfig.faceiddb.face_collection]


@pytest.fixture
def fixture_staff_collection(fixture_faceiddb, appconfig: AppConfigModel) -> AsyncIOMotorCollection:  # noqa: F811
    return fixture_faceiddb[appconfig.faceiddb.staff_collection]


@pytest.mark.asyncio
async def test_get_people_count(fixture_staff_collection, test_time):
    begin, end = test_time
    count = await get_people_count(fixture_staff_collection)
    assert count == 723, fixture_staff_collection.name


@pytest.mark.asyncio
async def test_get_inout_count(fixture_bodyfacename_collection, test_time):
    begin, end = test_time
    ret = await get_inout_count(fixture_bodyfacename_collection, begin, end)
    assert ret == 2
    ret = await get_inout_count(fixture_bodyfacename_collection, end, begin)
    assert ret == 0
    with pytest.raises(TypeError):
        ret = await get_inout_count(fixture_bodyfacename_collection, begin=None, end=end)
    with pytest.raises(TypeError):
        ret = await get_inout_count(fixture_bodyfacename_collection, begin=1, end=end)
    with pytest.raises(TypeError):
        ret = await get_inout_count(fixture_bodyfacename_collection, begin=begin, end=1)
    with pytest.raises(ValueError):
        ret = await get_inout_count(fixture_bodyfacename_collection, begin="1", end=end)


@pytest.mark.asyncio
async def test_get_stage1(fixture_staff_collection, avai_staff):
    query_params = QueryParamters()
    assert query_params.is_empty()

    query_params = QueryParamters(staffcodes=avai_staff)
    assert not query_params.is_empty()
    stage1 = query_find_staff(query_params)
    cursor1 = fixture_staff_collection.aggregate(stage1)
    count = 0
    async for document in cursor1:
        PersonInout.model_validate(document)
        count += 1

    assert count == len(avai_staff), json.dumps(stage1)

    # testcase 2
    custom_query = {"$and": [{"$eq": ["$unit", "BigHospital"]}, {"$eq": ["$department", "Mamachue"]}]}
    custom_query_string = json.dumps(custom_query)
    query_params = QueryParamters(custom_query=custom_query_string)
    assert not query_params.is_empty()
    stage2 = query_find_staff(query_params)
    cursor2 = fixture_staff_collection.aggregate(stage2)
    result = await cursor2.to_list(length=10000)
    assert len(result) == 5, json.dumps(stage2)


@pytest.mark.asyncio
async def test_get_people_inout(fixture_staff_collection, fixture_bodyfacename_collection, test_time, avai_staff):
    begin, end = test_time

    # testcase 1: empty staffcodes
    ret = await get_people_inout(
        fixture_staff_collection, fixture_bodyfacename_collection, QueryParamters(), begin, end
    )
    assert isinstance(ret, PersonInoutCollection)
    assert ret.count == 0
    assert len(ret.values) == 0

    # testcase 2: True staffcodes
    ret = await get_people_inout(
        fixture_staff_collection, fixture_bodyfacename_collection, QueryParamters(staffcodes=avai_staff), begin, end
    )
    assert isinstance(ret, PersonInoutCollection)
    assert ret.count == len(avai_staff)
    assert len(ret.values) == len(avai_staff)
    assert isinstance(ret.values[0], PersonInout)

    with pytest.raises(TypeError):
        await get_people_inout(fixture_staff_collection, fixture_bodyfacename_collection, avai_staff, begin, end=None)

    with pytest.raises(TypeError):
        await get_people_inout(
            fixture_staff_collection, fixture_bodyfacename_collection, avai_staff, begin=None, end=None
        )


@pytest.mark.asyncio
async def test_get_sample_count(fixture_staff_collection):
    count = await get_has_sample_count(fixture_staff_collection)
    assert count == 723, fixture_staff_collection.name


@pytest.mark.asyncio
async def test_get_should_checkinout_count(fixture_staff_collection):
    count = await get_should_checkinout_count(fixture_staff_collection)
    assert count == 723 - 2, fixture_staff_collection.name


@pytest.mark.asyncio
async def test_get_person_count_by_id(fixture_bodyfacename_collection):
    from datetime import datetime

    begin = datetime.fromisoformat("1990-12-27T00:00:00.000+00:00")
    end = datetime.fromisoformat("2990-12-27T00:00:00.000+00:00")
    # testcase: count all
    count = await get_person_count_by_id(fixture_bodyfacename_collection, None, begin, end, 0.1, False)
    assert count == 100
    # testcase: count one person
    count = await get_person_count_by_id(fixture_bodyfacename_collection, "267817", begin, end, 0.1, False)
    assert count == 48
    # testcase: count no one
    count = await get_person_count_by_id(fixture_bodyfacename_collection, "1", begin, end, 0.1, False)
    assert count == 0


@pytest.mark.asyncio
async def test_get_person_record_by_id(fixture_bodyfacename_collection, test_time):
    begin, end = test_time
    records = await get_person_record_by_id(fixture_bodyfacename_collection, None, begin, end, 0.1, False, limit=0)
    assert records.count == 100

    records = await get_person_record_by_id(fixture_bodyfacename_collection, None, begin, end, 0.1, False)
    assert records.count == 100

    records = await get_person_record_by_id(fixture_bodyfacename_collection, "267817", begin, end, 0.1, False)
    assert records.count == 48
    assert len(records.values) == 10
    records = await get_person_record_by_id(
        fixture_bodyfacename_collection, "267817", begin, end, 0.1, False, offset=45
    )
    assert records.count == 48
    assert len(records.values) == 3


@pytest.mark.asyncio
async def test_get_record_count_by_date_cam(fixture_bodyfacename_collection, test_time):
    begin, end = test_time
    records = await get_record_count_by_date_cam(fixture_bodyfacename_collection, None, begin, end, 0.1, False)
    assert records.count == 5

    records = await get_record_count_by_date_cam(fixture_bodyfacename_collection, "267817", begin, end, 0.1, False)
    assert records.count == 1
