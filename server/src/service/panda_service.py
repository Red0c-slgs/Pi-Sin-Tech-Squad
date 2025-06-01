from fastapi import HTTPException
from collections import defaultdict
import os
import tempfile

from rest.models.panda_data import LabelData
from rest.models.project_file import ProjectFileStatusType
from dao.project_file import ProjectFile, FileDefect
from dao.base import with_async_db_session

from service.s3 import S3
from utils.config import CONFIG
from utils.logger import get_logger

log = get_logger("YoloResultService")


class YoloResultService:
    def __init__(self):
        self.s3 = S3(CONFIG.s3)

    async def analysis_yolo_txt(self, file_id: int, txt: str) -> LabelData:
        log.info(f"Analysis YOLO for file: {file_id}")
        result = await self.report(file_id=file_id, txt=txt)
        await self.process_yolo_defects(file_id=file_id, yolo_content=txt)
        log.info(f"Analysis YOLO for file: {file_id} completed")
        return result

    @with_async_db_session
    async def report(self, file_id: int, txt: str) -> LabelData:
        if not txt:
            return ProjectFileStatusType.success # Текст пуст - все ок

        project_file = await ProjectFile.get_file_by_id(file_id)

        if not project_file:
            log.error(f"File {project_file} not found")
            raise HTTPException(status_code=404, detail="File not found")

        # Подсчет элементов
        total = self._analyze_yolo_labels(txt)
        # Вердикт
        verdict = ProjectFileStatusType.error if total > 0 else ProjectFileStatusType.success

        file_extension = ".txt"
        filename = os.path.splitext(project_file.s3_path)[0]

        s3_txt_path = f"{filename}{file_extension}"

        unique_filename = os.path.basename(s3_txt_path)

        temp_dir = tempfile.gettempdir()
        temp_file_path = os.path.join(temp_dir, unique_filename)

        with open(temp_file_path, "w") as temp_file:
            temp_file.write(txt)

        try:
            s3_txt_url = self.s3.upload_file(temp_file_path, s3_txt_path)
            await project_file.upload_txt(file_id=file_id, s3_txt_path=s3_txt_path, s3_txt_url=s3_txt_url)
            # Обновляем статус для фотки
            await project_file.update_file_status(file_id=file_id, status=verdict)
            os.remove(temp_file_path)

            log.info(f"Txt uploaded successfully: {s3_txt_url}")

        except Exception as e:
            if os.path.exists(temp_file_path):
                os.remove(temp_file_path)
            log.error(f"Error uploading txt: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Error uploading txt: {str(e)}")

        # Возвращаем результат
        return LabelData(s3_txt_path=s3_txt_path, label=txt)

    @staticmethod
    def _analyze_yolo_labels(text: str) -> int:
        defect_counts = 0
        for line in text.split("\n"): # Хз в чем дело, .splitline() и \n не работают
            parts = line.strip().split()
            clas = parts[0]
            if clas not in ["6", "7", "8"]:  # проверяем, что класс не эталон
                defect_counts += 1

        return defect_counts

    @staticmethod
    async def process_yolo_defects(file_id: int, yolo_content: str) -> None:
        """
        Парсит YOLO-разметку и сохраняет дефекты в БД
        """
        # Удаляем старые дефекты
        await ProjectFile.delete_file_defects(file_id)

        # Парсим новые дефекты
        defect_counts = defaultdict(int)
        for line in yolo_content.split("\n"):
            line = line.strip()
            if line:
                parts = line.split()
                if parts:
                    try:
                        class_id = int(parts[0])
                        defect_counts[class_id] += 1
                    except (ValueError, IndexError):
                        continue

        # Сохраняем в БД
        total = 0
        for class_id, count in defect_counts.items():
            await FileDefect.create(
                file_id=file_id,
                class_id=class_id,
                count=count
            )
            total += count

        # Обновляем общее количество
        await ProjectFile.update_defect_count(file_id, total)