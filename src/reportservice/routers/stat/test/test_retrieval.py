from datetime import datetime
import pytest
from ..retrieval import get_people_count, get_inout_count, get_dataframe


@pytest.mark.skip
@pytest.mark.asyncio
async def test_get_people_count(dbcolelction, test_time):
    begin, end = test_time
    await get_people_count(dbcolelction, begin, end)


@pytest.mark.asyncio
async def test_get_inout_count(dbcolelction, test_time):
    begin, end = test_time
    ret = await get_inout_count(dbcolelction, begin, end)
    assert ret == 2
    begin = None
    with pytest.raises(TypeError):
        ret = await get_inout_count(dbcolelction, begin, end)
    begin = 1
    with pytest.raises(TypeError):
        ret = await get_inout_count(dbcolelction, begin, end)

    begin = "1"
    with pytest.raises(ValueError):
        ret = await get_inout_count(dbcolelction, begin, end)


@pytest.mark.skip
@pytest.mark.asyncio
async def test_get_dataframe(dbcolelction, test_time):
    begin, end = test_time
    staffcodes = []
    await get_dataframe(dbcolelction, staffcodes, begin, end)
