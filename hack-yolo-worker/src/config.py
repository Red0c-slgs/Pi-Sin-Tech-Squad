import os
import logging

logger = logging.getLogger(__name__)

class Config:
    def __init__(self):
        self.YOLO_MAX_WORKERS = int(os.environ.get('MAX_WORKERS', 20))
        self.REPORT_URL = str(os.environ.get('REPORT_URL', 'http://0.0.0.0:5000'))

        self._validate_config()

    def _validate_config(self):
        required_fields = []

        missing_fields = []
        for field in required_fields:
            if getattr(self, field) is None:
                missing_fields.append(field)

        if missing_fields:
            error_msg = f"Отсутствуют обязательные переменные окружения: {', '.join(missing_fields)}"
            logger.error(error_msg)
            raise ValueError(error_msg)

CONFIG = Config()
