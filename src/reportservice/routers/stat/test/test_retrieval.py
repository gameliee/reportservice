from typing import List
import pytest
import pandas as pd
from ..retrieval import get_people_count, get_inout_count, get_people_inout
from ..models import PersonInout


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
    ret = await get_inout_count(dbinstance, staff_collection, bodyfacename_collection, end, begin)
    assert ret == 0
    with pytest.raises(TypeError):
        ret = await get_inout_count(dbinstance, staff_collection, bodyfacename_collection, begin=None, end=end)
    with pytest.raises(TypeError):
        ret = await get_inout_count(dbinstance, staff_collection, bodyfacename_collection, begin=1, end=end)
    with pytest.raises(TypeError):
        ret = await get_inout_count(dbinstance, staff_collection, bodyfacename_collection, begin=begin, end=1)
    with pytest.raises(ValueError):
        ret = await get_inout_count(dbinstance, staff_collection, bodyfacename_collection, begin="1", end=end)


@pytest.mark.asyncio
async def test_get_stat(dbinstance, appconfig, test_time, avai_staff):
    begin, end = test_time
    staff_collection = appconfig.faceiddb.staff_collection
    bodyfacename_collection = appconfig.faceiddb.face_collection

    # testcase 1: empty staffcodes
    ret = await get_people_inout(dbinstance, staff_collection, bodyfacename_collection, [], begin, end)
    assert isinstance(ret, List)
    assert len(ret) == 0

    # testcase 2: None staffcodes
    ret = await get_people_inout(dbinstance, staff_collection, bodyfacename_collection, None, begin, end)
    assert isinstance(ret, List)
    assert len(ret) == 0

    # testcase 3: True staffcodes
    ret = await get_people_inout(dbinstance, staff_collection, bodyfacename_collection, avai_staff, begin, end)
    assert isinstance(ret, List)
    assert len(ret) == len(avai_staff)
    assert isinstance(ret[0], PersonInout)

    with pytest.raises(TypeError):
        await get_people_inout(dbinstance, staff_collection, bodyfacename_collection, avai_staff, begin, end=None)

    with pytest.raises(TypeError):
        await get_people_inout(dbinstance, staff_collection, bodyfacename_collection, avai_staff, begin=None, end=None)
