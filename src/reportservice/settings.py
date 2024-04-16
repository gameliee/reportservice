"""load config"""

from pydantic import MongoDsn, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
from dynaconf import Dynaconf

dynasettings = Dynaconf(
    settings_file=["settings.toml", ".secret.toml"],
    environments=True,
)


class CommonSettingsModel(BaseSettings):
    LOG_FILE: str = "log/debug.log"
    APP_NAME: str = "FARM"
    DEBUG_MODE: bool = False  # watch for changes and auto reload the server
    PROFILING_ENABLED: bool = False  # Enable pyinstrument profiling
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

    @field_validator("DB_URL")
    @classmethod
    def validate_mongo_uri(cls, v: str) -> str:
        return str(MongoDsn(v))


class AppSettingsModel(CommonSettingsModel, ServerSettingsModel, DatabaseSettingsModel):
    model_config = SettingsConfigDict(extra="ignore")


settings = AppSettingsModel.model_validate(dynasettings.as_dict())
