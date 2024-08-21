import logging
import os
from logging.handlers import RotatingFileHandler

LOG_FILE_MAP = { "app_server.database_handler": "/logs/database_queries_processing.log", "others": "/logs/mmo_flask_app.log" }

PROJECT_PATH = os.environ.get("PROJECT_PATH")

def get_logger(__name__):
    file_name = PROJECT_PATH + str(LOG_FILE_MAP.get(__name__) or LOG_FILE_MAP.get("others"))
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.DEBUG)
    handler = RotatingFileHandler(file_name, maxBytes = 10000000, backupCount = 5)
    formatter = logging.Formatter(
            "[%(asctime)s] {%(pathname)s:%(funcName)20s():%(lineno)d} %(levelname)s - %(message)s")
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.info('Completed configuring logger()!')
    return logger

    # get_logger(__name__)
