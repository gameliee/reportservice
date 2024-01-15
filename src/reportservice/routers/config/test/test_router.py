import pytest
from fastapi import HTTPException
from ..router import validate_config
from ...common.config_models import AppConfigModel, FaceIDDBConfigModel, SmtpConfigsModel


@pytest.mark.asyncio
async def test_validate_settings():
    # invalid test case
    settings = AppConfigModel(
        faceiddb=FaceIDDBConfigModel(
            database="",
            staff_collection="",
            face_collection="",
        ),
        smtp=SmtpConfigsModel(
            enable=True,
            username="",
            account="a@a.com",
            password="",
            server="",
            port=0,
            useSSL=False,
        ),
    )

    with pytest.raises(HTTPException):
        await validate_config(settings)
