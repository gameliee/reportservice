import pytest
from .models import AppSettingsModel, FaceIDDBSettingsModel, SmtpSettingsModel


@pytest.fixture
def appconfig(collectionconfig, smtpconfig) -> AppSettingsModel:
    return AppSettingsModel(
        faceiddb=FaceIDDBSettingsModel.model_validate(collectionconfig),
        smtp=SmtpSettingsModel.model_validate(smtpconfig),
    )
