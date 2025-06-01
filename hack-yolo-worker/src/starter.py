# import logging
# import os
# import botocore

# from config import CONFIG
# from request import signal_server_start, signal_delete_service
# from s3 import download_yolo_weights
import uvicorn
from api import app

# logging.basicConfig(
#     level=logging.INFO,
#     format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
# )
# logger = logging.getLogger(__name__)



if __name__ == '__main__':
    try:
        # download_yolo_weights()
        # logger.info("Подготовка данных завершена успешно")
        uvicorn.run(app, host="0.0.0.0", port=8000)

    except Exception as e:
        # signal_delete_service()
        # logger.error(f"Произошла ошибка при подготовке данных: {e}")
        raise
