import pytest
from .config_models import AppConfigModel, FaceIDDBConfigModel, SmtpConfigsModel


@pytest.fixture
def appconfig(collectionconfig, smtpconfig) -> AppConfigModel:
    return AppConfigModel(
        faceiddb=FaceIDDBConfigModel.model_validate(collectionconfig),
        smtp=SmtpConfigsModel.model_validate(smtpconfig),
    )
