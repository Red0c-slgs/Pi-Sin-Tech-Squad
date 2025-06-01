import contextvars
import logging
import sys

import graypy  # type: ignore
from graypy.handler import BaseGELFHandler  # type: ignore

from utils.config import CONFIG

request_id_var = contextvars.ContextVar("request_id", default=0)


class GraylogFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord):
        record.app_name = CONFIG.logging.app_name
        record.request_id = request_id_var.get()
        return super().format(record)


graylog_handler: BaseGELFHandler | None = None  # type: ignore
if CONFIG.logging.graylog.enabled:
    if CONFIG.logging.graylog.udp:
        graylog_handler = graypy.GELFUDPHandler(CONFIG.logging.graylog.host, CONFIG.logging.graylog.port)  # type: ignore
    else:
        graylog_handler = graypy.GELFTCPHandler(CONFIG.logging.graylog.host, CONFIG.logging.graylog.port)  # type: ignore

    graylog_formatter = GraylogFormatter("[%(name)s]: %(message)s")
    graylog_handler.setFormatter(graylog_formatter)  # type: ignore

console_handler: logging.StreamHandler | None = None  # type: ignore
if CONFIG.logging.console.enabled:
    console_handler = logging.StreamHandler(sys.stdout)  # type: ignore
    console_handler.setFormatter(logging.Formatter("%(asctime)s [%(name)s] %(levelname)s: %(message)s"))

logging.getLogger().setLevel(CONFIG.logging.root_level)
for log, level in CONFIG.logging.levels.items():
    logging.getLogger(log).setLevel(level)


def get_logger(name: str) -> logging.Logger:
    logger = logging.getLogger(name)

    logger.propagate = False  # Global logger should not print messages again.

    # Avoiding log duplicates: do not add handlers again to already initialized logger
    # https://stackoverflow.com/questions/7173033/duplicate-log-output-when-using-python-logging-module
    if len(logger.handlers) != 0:
        return logger

    if console_handler:
        logger.addHandler(console_handler)  # type: ignore

    if graylog_handler:
        logger.addHandler(graylog_handler)  # type: ignore

    return logger


def get_logger_univorn():
    logging_config = {
        "version": 1,
        "disable_existing_loggers": False,
        "handlers": {
            "console": {
                "()": lambda: console_handler,  # type: ignore
            }
        },
        "root": {
            "level": "INFO",
            "handlers": ["console"],
        },
    }
    if CONFIG.logging.graylog.enabled:
        logging_config["handlers"]["graylog"] = {  # type: ignore
            "()": lambda: graylog_handler,  # type: ignore
        }
        logging_config["root"]["handlers"].append("graylog")  # type: ignore
    return logging_config
