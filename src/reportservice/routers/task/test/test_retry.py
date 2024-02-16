# import pytest
# from logging import Logger
# from apscheduler.schedulers.base import BaseScheduler
# from apscheduler.events import JobExecutionEvent, EVENT_JOB_ERROR
# from ..task import render_and_send_today, register_listerner

# @pytest.mark.asyncio
# async def test_render_and_send_today(testsettings, mocker):
#     logger = mocker.Mock(spec=Logger(name="testlogger"))
#     result = await render_and_send_today("contentid", testsettings, logger=logger)
