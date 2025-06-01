from fastapi import APIRouter, Depends, UploadFile, File, Path, Query, Response
from typing import Optional

from rest.models.project_file import ProjectFileData, ProjectFileListData
from service.file_service import FileService
from utils.logger import get_logger

log = get_logger("FileEndpoint")

router = APIRouter(prefix="/projects/{project_id}/files", tags=["files"])


@router.post("", response_model=ProjectFileData)
async def upload_file(
    project_id: int = Path(..., description="Project ID"),
    file: UploadFile = File(...),
    service: FileService = Depends()
):
    """Загрузка файла (фото) в проект"""
    log.info(f"Received request to upload file {file.filename} to project {project_id}")
    result = await service.upload_file(project_id, file)
    log.info(f"File uploaded successfully with ID {result.id}")
    return result


@router.get("", response_model=ProjectFileListData)
async def get_project_files(
    project_id: int = Path(..., description="Project ID"),
    filename: Optional[str] = Query(None, description="Фильтр по имени файла"),
    status: Optional[str] = Query(None, description="Фильтр по статусу файла", enum=["processing", "success", "error"]),
    page: int = Query(1, ge=1, description="Номер страницы"),
    size: int = Query(20, ge=1, le=100, description="Количество элементов на странице"),
    service: FileService = Depends()
) -> ProjectFileListData:
    """Получить список файлов с возможностью фильтрации"""
    log.info(f"Getting files for project {project_id}, filters: filename={filename}, status={status}, page={page}, size={size}")
    result = await service.get_project_files(
        project_id=project_id,
        filename=filename,
        status=status,
        page=page,
        size=size
    )
    log.info(f"Retrieved {len(result.items)} files for project {project_id}")
    return result


@router.get("/{file_id}", response_model=ProjectFileData)
async def get_file(
    project_id: int = Path(..., description="Project ID"),
    file_id: int = Path(..., description="File ID"),
    service: FileService = Depends()
):
    """Получить файл по ID"""
    log.info(f"Received request to get file {file_id} from project {project_id}")
    result = await service.get_file(file_id)
    log.info(f"Retrieved file {file_id}")
    return result


@router.delete("/{file_id}")
async def delete_file(
    project_id: int = Path(..., description="Project ID"),
    file_id: int = Path(..., description="File ID"),
    service: FileService = Depends()
):
    """Удалить файл по ID"""
    log.info(f"Received request to delete file {file_id} from project {project_id}")
    await service.delete_file(file_id)
    log.info(f"File {file_id} deleted successfully")
    return {"message": "File deleted successfully"}


@router.post("/{file_id}/training", response_model=ProjectFileData)
async def training_file(
    project_id: int = Path(..., description="Project ID"),
    file_id: int = Path(..., description="File ID"),
    service: FileService = Depends()
):
    """Отправить файл для дообучения модели"""
    log.info(f"Received request to training file {file_id} from project {project_id}")
    result = await service.training_file(project_id, file_id)
    log.info(f"File {file_id} uploaded to training")
    return result


@router.get("/{file_id}/report")
async def get_report_for_file(project_id: int, file_id: int, service: FileService = Depends()) -> Response:
    """Создать и скачать отчет о файле в формате PDF"""
    log.info(f"Received request to get report for file {file_id} from project {project_id}")
    pdf_bytes = await service.get_report(project_id=project_id, file_id=file_id)
    log.info(f"Retrieved PDF report for file {file_id} from project {project_id}")
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename=report_{file_id}.pdf"})


@router.post("/{file_id}", response_model=ProjectFileData)
async def process_file(file_id: int, service: FileService = Depends()) -> ProjectFileData:
    """Отправляет файл на обработку (можно использовать для повторной обработки)"""
    log.info(f"Started reprocessing file {file_id}")
    result = await service.process_file(file_id=file_id)
    log.info(f"Reprocessing file {file_id} completed!")
    return result