import pytest
from fastapi import HTTPException
from ..router import validate_settings
from ..models import AppSettingsModel, FaceIDDBSettingsModel, SmtpSettingsModel


@pytest.mark.asyncio
async def test_validate_settings():
    # invalid test case
    settings = AppSettingsModel(
        faceiddb=FaceIDDBSettingsModel(
            staff_collection="",
            face_collection="",
        ),
        smtp=SmtpSettingsModel(
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
        await validate_settings(settings)
