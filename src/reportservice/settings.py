"""load config"""
from dynaconf import Dynaconf
from pydantic_settings import BaseSettings, SettingsConfigDict

dynasettings = Dynaconf(
    settings_file=["settings.toml", ".secret.toml"],
    environments=True,
)


class CommonSettings(BaseSettings):
    LOG_FILE: str = "log/debug.log"
    APP_NAME: str = "FARM"
    DEBUG_MODE: bool = False
    WORKERS: int = 1


class ServerSettings(BaseSettings):
    HOST: str = "0.0.0.0"
    PORT: int = 3002


class DatabaseSettings(BaseSettings):
    DB_URL: str
    DB_NAME: str
    DB_COLLECTION_SETTINGS: str


class AppSettings(CommonSettings, ServerSettings, DatabaseSettings):
    model_config = SettingsConfigDict(extra="ignore")


settings = AppSettings.model_validate(dynasettings.as_dict())
