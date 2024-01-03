"""sent logs to console, file, and loki"""
import os
import sys
import logging
import logging.config
from logging.handlers import RotatingFileHandler
from .settings import settings

LOG_FILE = settings.LOG_FILE
LOG_NAME = settings.APP_NAME

# logger
slogger = logging.getLogger(LOG_NAME)
slogger.setLevel(logging.DEBUG)

# formatter
formatter = logging.Formatter("[%(asctime)s] %(levelname)s [%(name)s.%(funcName)s:%(lineno)d] %(message)s")

# handlers
consoleHandler = logging.StreamHandler(sys.stdout)
consoleHandler.setLevel(logging.INFO)
consoleHandler.setFormatter(formatter)

if not os.path.exists(os.path.dirname(LOG_FILE)):
    os.makedirs(os.path.dirname(LOG_FILE))
fileHandler = RotatingFileHandler(filename=LOG_FILE, mode="a", maxBytes=2000000, backupCount=100)
fileHandler.setLevel(logging.DEBUG)
fileHandler.setFormatter(formatter)

# add handlers to loggers
slogger.addHandler(consoleHandler)
slogger.addHandler(fileHandler)


def my_handler(_type, _value, _tb):
    """catch all uncaught exception"""
    slogger.fatal("Uncaught exception: ", exc_info=(_type, _value, _tb))


sys.excepthook = my_handler
