import pytest
import pandas as pd
from ..retrieval import get_people_count, get_inout_count, get_dataframe
from ..models import DFConst


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
async def test_get_dataframe(dbinstance, appconfig, test_time):
    begin, end = test_time
    staff_collection = appconfig.faceiddb.staff_collection
    bodyfacename_collection = appconfig.faceiddb.face_collection
    staffcodes = []
    ret = await get_dataframe(dbinstance, staff_collection, bodyfacename_collection, staffcodes, begin, end)
    assert isinstance(ret, pd.DataFrame)
    assert len(ret) == 0
    assert DFConst.STAFF in ret.columns
    assert DFConst.FIRST in ret.columns
    assert DFConst.LASTT in ret.columns
    assert DFConst.SAMPL in ret.columns

    ret = await get_dataframe(dbinstance, staff_collection, bodyfacename_collection, None, begin, end)
    assert isinstance(ret, pd.DataFrame)
    assert len(ret) == 0
    assert DFConst.STAFF in ret.columns
    assert DFConst.FIRST in ret.columns
    assert DFConst.LASTT in ret.columns
    assert DFConst.SAMPL in ret.columns

    with pytest.raises(TypeError):
        await get_dataframe(dbinstance, staff_collection, bodyfacename_collection, staffcodes, begin, end=None)

    with pytest.raises(TypeError):
        await get_dataframe(dbinstance, staff_collection, bodyfacename_collection, staffcodes, begin=None, end=None)
