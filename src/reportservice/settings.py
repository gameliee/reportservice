"""load config"""
from dynaconf import Dynaconf
from pydantic_settings import BaseSettings, SettingsConfigDict

dynasettings = Dynaconf(
    settings_file=["settings.toml", ".secret.toml"],
    environments=True,
)


class CommonSettingsModel(BaseSettings):
    LOG_FILE: str = "log/debug.log"
    APP_NAME: str = "FARM"
    DEBUG_MODE: bool = False
    WORKERS: int = 1


class ServerSettingsModel(BaseSettings):
    HOST: str = "0.0.0.0"
    PORT: int = 3002


class DatabaseSettingsModel(BaseSettings):
    DB_URL: str
    DB_REPORT_NAME: str
    DB_COLLECTION_CONFIG: str
    DB_COLLECTION_CONTENT: str
    DB_COLLECTION_TASK: str
    DB_COLLECTION_SCHEDULER: str
    DB_COLLECTION_LOG: str


class AppSettingsModel(CommonSettingsModel, ServerSettingsModel, DatabaseSettingsModel):
    model_config = SettingsConfigDict(extra="ignore")


settings = AppSettingsModel.model_validate(dynasettings.as_dict())
