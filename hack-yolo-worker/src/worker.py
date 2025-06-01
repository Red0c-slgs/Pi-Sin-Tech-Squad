import os

import httpx
import requests
import imghdr
import logging

from config import CONFIG
from dto import RecognizeRequest
from yolo import YOLOv11SegPredictor

logger = logging.getLogger(__name__)

class Worker():
    def __init__(self):
        path = self.download_weight()
        self.yolo_service = YOLOv11SegPredictor(path)

    def download_weight(self) -> str:
        url = "http://94.154.128.76:9001/api/v1/buckets/yolo/objects/download?prefix=best.pt"
        filename = "best.pt"
        save_dir = "weights"
        os.makedirs(save_dir, exist_ok=True)
        filepath = os.path.join(save_dir, filename)

        response = requests.get(url, stream=True)
        response.raise_for_status()

        with open(filepath, "wb") as f:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)

        return filepath

    def worker_start(self, data: RecognizeRequest):
        try:
            response = requests.get(data['image_url'], stream=True)
            response.raise_for_status()

            image_content = response.content

            image_type = imghdr.what(None, h=image_content)

            if image_type not in ['jpeg', 'png']:
                logger.error(f"Invalid image format: {image_type}. Only JPEG and PNG are supported.")
                return False

            response = self.yolo_service.predict(image_content)
            url = f'{CONFIG.REPORT_URL}/yolo'
            params = {
                "project_id": data['project_id'],
                "file_id": data['image_id'],
                "label": response,
            }

            with httpx.Client() as client:
                response = client.post(url, params=params)
                response.raise_for_status()
                recognize_result = response.json()

        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to download file from URL: {e}")
            return False
        except Exception as e:
            logger.error(f"Error processing image: {e}")
            return False

WORKER = Worker()