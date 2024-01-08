from ..models import AppSettingsModelUpdate, AppSettingsModel, SmtpSettingsModel, SmtpSettingsModelUpdate


def test_SmtpSettingsModel():
    base = SmtpSettingsModel.model_validate(
        {
            "account": "testnv@example.com",
            "enable": "false",
            "password": "",
            "port": 0,
            "server": "",
            "username": "",
            "useSSL": False,
        }
    )

    update = SmtpSettingsModelUpdate.model_validate({"username": "hola"})
    base.update(update)
    SmtpSettingsModel.model_construct(**update.model_dump())
    assert base.username == update.username
    assert base.account is not None


def test_AppSettingsModelUpdate_merge_into_AppSettingsModel():
    base = AppSettingsModel.model_validate(
        {
            "faceiddb": {
                "staff_collection": "BodyFaceName",
                "face_collection": "staff",
            },
            "smtp": {
                "enable": False,
                "username": "",
                "account": "testnv@example.com",
                "password": "",
                "server": "",
                "port": 0,
                "useSSL": False,
            },
        }
    )
    update = AppSettingsModelUpdate.model_validate({"smtp": {"username": "lazada"}})
    base.update(update)
    assert base.smtp.username == update.smtp.username
    assert base.faceiddb is not None
