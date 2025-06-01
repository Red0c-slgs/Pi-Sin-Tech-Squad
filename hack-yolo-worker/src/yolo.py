from ultralytics import YOLO
import cv2
import numpy as np
from typing import Union, List


class YOLOv11SegPredictor:
    def __init__(self, model_path: str):
        self.model = YOLO(model_path)
        self.device = "cuda"

    def predict(self, image: Union[str, np.ndarray, bytes]) -> str:
        if isinstance(image, str):
            img = cv2.imread(image)
            if img is None:
                raise FileNotFoundError(f"Изображение не найдено по пути: {image}")
        elif isinstance(image, bytes):
            nparr = np.frombuffer(image, np.uint8)
            img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            if img is None:
                raise ValueError("Невозможно декодировать изображение из bytes")
        else:
            img = image

        result = self.model(img)[0]

        names = self.model.names

        lines = []
        if result.masks and result.masks.xyn:
            for i, polygon in enumerate(result.masks.xyn):
                cls_id = int(result.boxes.cls[i])
                flat_coords = " ".join(f"{x:.6f} {y:.6f}" for x, y in polygon)
                line = f"{cls_id} {flat_coords}"
                lines.append(line)

        return "\n".join(lines)