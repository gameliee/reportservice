from fastapi import FastAPI
from logging import Logger
from pyinstrument import Profiler
from .settings import AppSettingsModel


class ExtendedFastAPI(FastAPI):
    def __init__(self, settings: AppSettingsModel, logger: Logger, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.settings = settings
        self.logger = logger
