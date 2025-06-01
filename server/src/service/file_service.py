import uuid
import os
import tempfile
from collections import defaultdict
from io import BytesIO

import httpx
from fastapi import UploadFile, HTTPException
from typing import Optional, Dict
from pathlib import Path

from dao.base import with_async_db_session
from dao.project_file import ProjectFile
from dao.project import Project
from rest.models.project_file import ProjectFileData, ProjectFileListData, ProjectFileStatusType
from rest.models.panda_data import LabelData, DefectType
from service.s3 import S3
from service.image_service import create_icon
from service.panda_service import YoloResultService
from utils.logger import get_logger
from utils.config import CONFIG

from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

# Проверка
font_path = Path(__file__).parent / "fonts" / "DejaVuSans.ttf"
if not font_path.exists():
    raise FileNotFoundError(f"Шрифт не найден по пути: {font_path}")


log = get_logger("FileService")
service_url = CONFIG.recognize_service

def set_service_url(url):
    global service_url
    service_url = url

class FileService:
    def __init__(self):
        self.s3 = S3(CONFIG.s3)
        self.training_bucket = "train-data-dop"

    @with_async_db_session
    async def upload_file(self, project_id: int, file: UploadFile) -> ProjectFileData:
        log.info(f"Uploading file {file.filename} for project {project_id}")

        project = await Project.get_project_by_id(project_id)
        if not project:
            log.error(f"Project {project_id} not found")
            raise HTTPException(status_code=404, detail="Project not found")

        file_extension = os.path.splitext(file.filename)[1] if file.filename else ""
        unique_filename = f"{uuid.uuid4()}{file_extension}"


        s3_path = f"{project_id}/{unique_filename}"
        s3_icon_path = f"{project_id}/icon_{unique_filename}"

        temp_dir = tempfile.gettempdir()
        temp_file_path = os.path.join(temp_dir, unique_filename)

        with open(temp_file_path, "wb") as temp_file:
            content = await file.read()
            temp_file.write(content)

        icon_temp_path = await create_icon(temp_dir, unique_filename)

        try:
            s3_url = self.s3.upload_file(temp_file_path, s3_path)
            s3_icon_url = self.s3.upload_file(icon_temp_path, s3_icon_path)

            project_file = await ProjectFile.create_file(
                project_id=project_id,
                filename=file.filename,
                s3_path=s3_path,
                s3_url=s3_url,
                s3_icon_path=s3_icon_path,
                s3_icon_url=s3_icon_url
            )
            os.remove(temp_file_path)

            log.info(f"File uploaded successfully: {s3_url}")

            return project_file.to_api()

        except Exception as e:
            if os.path.exists(temp_file_path):
                os.remove(temp_file_path)
            log.error(f"Error uploading file: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Error uploading file: {str(e)}")

    @with_async_db_session
    async def upload_txt(self, project_id: int, file_id: int, text: UploadFile) -> LabelData:
        log.info(f"Uploading txt {text.filename} for file {file_id}")
        project_file = await ProjectFile.get_file_by_id(file_id)

        if not project_file:
            log.error(f"File {project_file} not found")
            raise HTTPException(status_code=404, detail="File not found")

        file_extension = ".txt"
        filename = os.path.splitext(project_file.s3_path)[0]

        s3_txt_path = f"{filename}{file_extension}"

        unique_filename = os.path.basename(s3_txt_path)

        temp_dir = tempfile.gettempdir()
        temp_file_path = os.path.join(temp_dir, unique_filename)

        content = await text.read()

        result = await YoloResultService.analysis_yolo_txt(file_id=file_id, txt=content)

        return result

    async def delete_file(self, file_id: int) -> None:
        log.info(f"Deleting file with ID {file_id}")
        try:
            file_record = await ProjectFile.get_file_by_id(file_id)
            if not file_record:
                log.error(f"File with ID {file_id} not found")
                raise HTTPException(status_code=404, detail="File not found")

            self.s3.delete(file_record.s3_path)
            self.s3.delete(file_record.s3_icon_path)
            self.s3.delete(file_record.s3_txt_path)

            await ProjectFile.delete_file_by_id(file_id)

            log.info(f"File {file_id} deleted successfully")
        except Exception as e:
            log.error(f"Error deleting file: {str(e)}")
            # raise HTTPException(status_code=500, detail=f"Error deleting file: {str(e)}")

    @staticmethod
    async def get_file(file_id: int) -> ProjectFileData:
        log.info(f"Getting file with ID {file_id}")

        file_record = await ProjectFile.get_file_by_id(file_id)
        if not file_record:
            log.error(f"File with ID {file_id} not found")
            raise HTTPException(status_code=404, detail="File not found")

        return file_record.to_api(label= await FileService.get_label(s3_txt_path=file_record.s3_txt_path))

    @staticmethod
    async def get_project_files(project_id: int, filename: Optional[str] = None,
                                status: Optional[str] = None, defect_type: Optional[str] = None,
                                min_defects: Optional[int] = None, max_defects: Optional[int] = None, page: int = 1,
                                size: int = 20, to_delete: bool = False) -> ProjectFileListData | list:
        log.info(f"Getting files for project {project_id}")

        project = await Project.get_project_by_id(project_id)
        if not project:
            log.error(f"Project {project_id} not found")
            raise HTTPException(status_code=404, detail="Project not found")

        files, total = await ProjectFile.get_files_by_project_id(project_id=project_id, filename=filename,
                                                                 status=status, defect_type=defect_type,
                                                                 min_defects=min_defects, max_defects=max_defects,
                                                                 page=page,size=size)

        if to_delete:
            file_list = [file for file in files]
            return file_list

        file_list = [file.to_api(label= '') for file in files]

        # Получаем статистику по дефектам
        defect_stats = await ProjectFile.get_defect_stats(project_id)

        total_defects = sum(stat.count for stat in defect_stats)

        return ProjectFileListData(
            items=file_list,
            total=total,
            page=page,
            size=size,
            defect_statistics=defect_stats,
            total_defects=total_defects
        )

    @staticmethod
    @with_async_db_session
    async def get_label(s3_txt_path: str) -> str:
        """
        Возвращает строку с полным содержимым текстового файла.
        """
        if not s3_txt_path:
            return ""

        log.info(f"Чтение содержимого из файла {s3_txt_path}")

        try:
            content = S3(CONFIG.s3).get_file_content_as_str(s3_txt_path)
            return content
        except Exception as e:
            log.error(f"Ошибка при чтении файла {s3_txt_path}: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Не удалось прочитать файл: {str(e)}")

    @with_async_db_session
    async def process_file(self, file_id: int, not_processing: bool = False) -> ProjectFileData:
        """
        Запускает обработку файла
        """
        log.info(f"Processing file with ID {file_id}")

        file_record = await ProjectFile.get_file_by_id(file_id)
        if not file_record:
            log.error(f"File with ID {file_id} not found")
            raise HTTPException(status_code=404, detail="File not found")

        if not_processing and file_record.status == ProjectFileStatusType.processing:
            log.error(f"File {file_id} is already being processed")
            raise HTTPException(status_code=400, detail="File is already being processed")


        try:
            # Обновляем статус файла на "в обработке"
            await ProjectFile.update_file_status(file_id=file_id, status=ProjectFileStatusType.processing)

            url = service_url + "/recognize"
            payload = {
                "image_url": file_record.s3_url,
                "image_id": file_record.id,
                "project_id": file_record.project_id,
            }

            async with httpx.AsyncClient() as client:
                response = await client.post(url, json=payload)
                response.raise_for_status()
                recognize_result = response.json()

            if await FileService._is_error(file_record.s3_txt_path):
                await ProjectFile.update_file_status(file_id=file_id, status=ProjectFileStatusType.error)
            else:
                await ProjectFile.update_file_status(file_id=file_id, status=ProjectFileStatusType.success)

            log.info(f"File {file_id} processing started")

            # Возвращаем обновленные данные файла
            updated_file = await ProjectFile.get_file_by_id(file_id)
            return updated_file.to_api()

        except Exception as e:
            # В случае ошибки хз, просто пишем ошибку
            log.error(f"Error processing file {file_id}: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Error processing file: {str(e)}")

    @with_async_db_session
    async def training_file(self, project_id: int, file_id: int) -> ProjectFileData:
        """Загружает файлы в s3 для дообучения"""
        log.info(f"Training file with ID {file_id}")

        file_record = await ProjectFile.get_file_by_id(file_id)

        # Проверка на существование
        if not file_record:
            log.error(f"File with ID {file_id} not found")
            raise HTTPException(status_code=404, detail="File not found")

        # Перенесение
        source_keys = {"img": file_record.s3_path, "txt": file_record.s3_txt_path}

        file_extension = os.path.splitext(file_record.filename)[1]
        txt_extension = ".txt"
        filename = os.path.splitext(file_record.s3_path)[0]

        s3_txt_path = f"{filename}{txt_extension}"
        s3_img_path = f"{filename}{file_extension}"

        dest_keys = {"img": s3_img_path, "txt": s3_txt_path}

        try:
            # 1. Копируем файл в новый бакет
            copy_source = {'Bucket': self.s3.s3_config.bucket, 'Key': source_keys["img"]}
            self.s3.s3_client.copy_object(
                Bucket=self.training_bucket,
                Key=dest_keys["img"],
                CopySource=copy_source
            )
            copy_source = {'Bucket': self.s3.s3_config.bucket, 'Key': source_keys["txt"]}
            self.s3.s3_client.copy_object(
                Bucket=self.training_bucket,
                Key=dest_keys["txt"],
                CopySource=copy_source
            )

            # # 2. Удаляем оригинал
            # self.s3.s3_client.delete_object(Bucket=self.s3.s3_config.bucket, Key=source_keys["img"])

        except Exception as e:
            print(f"Error moving file: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Error moving file: {str(e)}")

        result = await ProjectFile.get_file_by_id(file_id)

        return result.to_api()

    @with_async_db_session
    async def get_report(self, project_id: int, file_id: int) -> bytes:
        """Возвращает отчет в формате .pdf с анализом дефектов как байты"""
        log.info(f"Getting report for file {file_id} from project {project_id}")

        # Получаем данные файла
        file = await ProjectFile.get_file_by_id(file_id)
        label = self.s3.get_file_content_as_str(file.s3_txt_path)

        # Инициализация стилей PDF
        styles = self._init_pdf_styles()

        # Анализ данных и подготовка контента
        defect_data = self._analyze_yolo_labels(label)
        summary_table = self._build_summary_table(file, defect_data, styles['CyrillicStyle'])
        full_table = self._generate_full_defects_table(label, styles['CyrillicStyle'])

        # Создаем PDF документ в памяти
        pdf_bytes = self._create_pdf_document(
            file=file,
            project_id=project_id,
            styles=styles,
            summary_table=summary_table,
            full_table=full_table
        )

        return pdf_bytes

    @staticmethod
    def _init_pdf_styles():
        """Инициализирует стили для PDF документа"""
        font_path = Path(__file__).parent / "fonts" / "DejaVuSans.ttf"
        pdfmetrics.registerFont(TTFont("DejaVu", str(font_path)))

        styles = getSampleStyleSheet()
        styles.add(ParagraphStyle(
            name="CyrillicStyle",
            fontName="DejaVu",
            fontSize=12,
            leading=14,
            encoding="UTF-8"
        ))
        return styles

    def _build_summary_table(self, file, defect_data, style):
        """Строит сводную таблицу дефектов"""
        table_data = [[
            Paragraph("Тип дефекта", style),
            Paragraph("Количество", style),
            Paragraph("Процент", style)
        ]]

        for class_id, count in defect_data.items():
            defect_type = DefectType.get_by_id(class_id)
            if defect_type:
                percentage = (count / file.defect_count) * 100 if file.defect_count > 0 else 0
                table_data.append([
                    Paragraph(defect_type.defect, style),
                    Paragraph(str(count), style),
                    Paragraph(f"{percentage:.1f}%", style)
                ])

        table_data.append([
            Paragraph("Всего", style),
            Paragraph(str(file.defect_count), style),
            Paragraph("100%", style)
        ])

        table = Table(table_data)
        self._apply_table_style(table, header_color=colors.grey, is_summary_table=True)
        return table

    def _generate_full_defects_table(self, yolo_text, style):
        """Генерирует полную таблицу дефектов с координатами"""
        table_data = [[
            Paragraph("Тип дефекта", style),
            Paragraph("Координаты", style)
        ]]

        for line in yolo_text.split("\n"):
            parts = line.strip().split()
            if parts:
                defect_type = DefectType.get_by_id(int(parts[0]))
                if defect_type:
                    table_data.append([
                        Paragraph(defect_type.defect, style),
                        Paragraph(" ".join(parts[1:]), style)
                    ])

        table = Table(table_data)
        self._apply_table_style(table, header_color=colors.grey, is_summary_table=False)
        return table

    @staticmethod
    def _apply_table_style(table, header_color, is_summary_table=True):
        """Применяет единый стиль к таблице"""
        style = [
            ('BACKGROUND', (0, 0), (-1, 0), header_color),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('FONTNAME', (0, 0), (-1, -1), 'DejaVu'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('FONTSIZE', (0, 1), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ]

        # Добавляем стили только для сводной таблицы
        if is_summary_table:
            style.extend([
                ('BACKGROUND', (0, 1), (-1, -2), colors.beige),
                ('BACKGROUND', (0, -1), (-1, -1), colors.lightgrey),
            ])
        else:
            # Для полной таблицы - просто бежевый фон всех строк кроме заголовка
            style.append(('BACKGROUND', (0, 1), (-1, -1), colors.beige))

        table.setStyle(TableStyle(style))

    @staticmethod
    def _create_pdf_document(file, project_id, styles, summary_table, full_table):
        """Создает PDF документ и возвращает его в виде байтов"""
        buffer = BytesIO()

        doc = SimpleDocTemplate(buffer, pagesize=letter)
        elements = [
            Paragraph(f"Отчет по дефектам для файла: {file.filename}", styles['CyrillicStyle']),
            Paragraph(f"Проект ID: {project_id}", styles['CyrillicStyle']),
            Spacer(1, 12),
            summary_table,
            Spacer(1, 12),
            Paragraph("Полная статистика", styles['CyrillicStyle']),
            full_table
        ]

        doc.build(elements)
        buffer.seek(0)
        return buffer.getvalue()

    @staticmethod
    def _analyze_yolo_labels(yolo_text: str) -> Dict:
        """Анализирует YOLO разметку и возвращает статистику по классам"""
        defect_counts = defaultdict(int)
        for line in yolo_text.split("\n"):
            parts = line.strip().split()
            if parts:
                defect_counts[int(parts[0])] += 1
        return defect_counts

    @staticmethod
    async def _is_error(s3_txt_path: str) -> bool:
        text = await FileService.get_label(s3_txt_path=s3_txt_path)
        for line in text.split("\n"):  # Хз в чем дело, .splitline() и \n не работают
            parts = line.strip().split()
            clas = parts[0]
            if clas not in ["6", "7", "8"]:  # проверяем, что класс не эталон
                return True
        return False