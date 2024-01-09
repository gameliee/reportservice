from datetime import datetime
import pytest
from ..retrieval import get_people_count, get_inout_count, get_dataframe


@pytest.mark.asyncio
async def test_get_people_count(dbinstance, appconfig, test_time):
    begin, end = test_time
    count = await get_people_count(
        dbinstance,
        staff_collection=appconfig.faceiddb.staff_collection,
        bodyfacename_collection=appconfig.faceiddb.face_collection,
        begin=begin,
        end=end,
    )
    assert count == 3


@pytest.mark.asyncio
async def test_get_inout_count(dbinstance, appconfig, test_time):
    begin, end = test_time
    staff_collection = appconfig.faceiddb.staff_collection
    bodyfacename_collection = appconfig.faceiddb.face_collection
    ret = await get_inout_count(dbinstance, staff_collection, bodyfacename_collection, begin, end)
    assert ret == 2
    begin = None
    with pytest.raises(TypeError):
        ret = await get_inout_count(dbinstance, staff_collection, bodyfacename_collection, begin, end)
    begin = 1
    with pytest.raises(TypeError):
        ret = await get_inout_count(dbinstance, staff_collection, bodyfacename_collection, begin, end)

    begin = "1"
    with pytest.raises(ValueError):
        ret = await get_inout_count(dbinstance, staff_collection, bodyfacename_collection, begin, end)


@pytest.mark.asyncio
async def test_get_dataframe(dbinstance, appconfig, test_time):
    begin, end = test_time
    staff_collection = appconfig.faceiddb.staff_collection
    bodyfacename_collection = appconfig.faceiddb.face_collection
    staffcodes = []
    await get_dataframe(dbinstance, staff_collection, bodyfacename_collection, staffcodes, begin, end)
