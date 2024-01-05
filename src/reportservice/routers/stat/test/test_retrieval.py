from datetime import datetime
import pytest
from ..retrieval import get_inout_count


@pytest.mark.asyncio
async def test_get_inout_count(dbcolelction):
    begin = datetime.fromisoformat("2023-12-27T00:00:00.000+00:00")
    end = datetime.fromisoformat("2023-12-27T23:59:59.999+00:00")
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
