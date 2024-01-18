from typing import List
import pytest
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorCollection, AsyncIOMotorDatabase
from ..retrieval import get_people_count, get_inout_count, get_people_inout
from ..models import PersonInout, PersonInoutCollection
from ...common import AppConfigModel
from ...common.conftest import appconfig


@pytest.fixture
def fixture_faceiddb(dburi, testsettings, collectionconfig) -> AsyncIOMotorDatabase:
    mongodb_client = AsyncIOMotorClient(dburi, uuidRepresentation="standard")
    faceid_database_name = collectionconfig["database"]
    mongodb: AsyncIOMotorDatabase = mongodb_client[faceid_database_name]
    return mongodb


@pytest.fixture
def fixture_bodyfacename_collection(
    fixture_faceiddb, appconfig: AppConfigModel  # noqa: F811
) -> AsyncIOMotorCollection:
    return fixture_faceiddb[appconfig.faceiddb.face_collection]


@pytest.fixture
def fixture_staff_collection(fixture_faceiddb, appconfig: AppConfigModel) -> AsyncIOMotorCollection:  # noqa: F811
    return fixture_faceiddb[appconfig.faceiddb.staff_collection]


@pytest.mark.asyncio
async def test_get_people_count(fixture_staff_collection, test_time):
    begin, end = test_time
    count = await get_people_count(
        fixture_staff_collection,
        begin=begin,
        end=end,
    )
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
async def test_get_people_inout(fixture_staff_collection, fixture_bodyfacename_collection, test_time, avai_staff):
    begin, end = test_time

    # testcase 1: empty staffcodes
    ret = await get_people_inout(fixture_staff_collection, fixture_bodyfacename_collection, [], begin, end)
    assert isinstance(ret, PersonInoutCollection)
    assert ret.count == 0
    assert len(ret.values) == 0

    # testcase 2: None staffcodes
    ret = await get_people_inout(fixture_staff_collection, fixture_bodyfacename_collection, None, begin, end)
    assert isinstance(ret, PersonInoutCollection)
    assert ret.count == 0
    assert len(ret.values) == 0

    # testcase 3: True staffcodes
    ret = await get_people_inout(fixture_staff_collection, fixture_bodyfacename_collection, avai_staff, begin, end)
    assert isinstance(ret, PersonInoutCollection)
    assert ret.count == len(avai_staff)
    assert len(ret.values) == len(avai_staff)
    assert isinstance(ret[0], PersonInout)

    with pytest.raises(TypeError):
        await get_people_inout(fixture_staff_collection, fixture_bodyfacename_collection, avai_staff, begin, end=None)

    with pytest.raises(TypeError):
        await get_people_inout(
            fixture_staff_collection, fixture_bodyfacename_collection, avai_staff, begin=None, end=None
        )
