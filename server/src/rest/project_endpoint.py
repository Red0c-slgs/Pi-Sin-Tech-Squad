from fastapi import APIRouter, Depends, Query
from typing import Optional
from datetime import datetime

from rest.models.project import ProjectData, ProjectListData, CreateProjectData
from rest.models.project_file import ProjectFileListData
from service.file_service import FileService
from service.project_service import ProjectService

from utils.logger import get_logger

router = APIRouter(prefix="/api/projects", tags=["projects"])
log = get_logger("project_endpoint")


@router.post("", response_model=ProjectData)
async def create_project(create_project_data: CreateProjectData, service: ProjectService = Depends()) -> ProjectData:
    """Создать проект"""
    log.info(f"Creating project with data: {create_project_data}")
    result = await service.create_project(create_project_data)
    log.info(f"Project created: {result}")
    return result


@router.get("", response_model=ProjectListData)
async def search_projects(
    name: Optional[str] = Query(None, description="Фильтр по названию проекта"),
    status_files: Optional[str] = Query(None, description="Фильтр по статусу файлов", enum=["processing", "success", "error"]),
    start_date: Optional[datetime] = Query(None, description="Дата начала периода (включительно)"),
    end_date: Optional[datetime] = Query(None, description="Дата окончания периода (включительно)"),
    page: int = Query(1, ge=1, description="Номер страницы"),
    size: int = Query(20, ge=1, le=100, description="Количество элементов на странице"),
    service: ProjectService = Depends()
) -> ProjectListData:
    """Получить список проектов с возможностью фильтрации"""
    log.info(f"Searching projects: name={name}, date_range={start_date}-{end_date}, page={page}, size={size}")
    result = await service.search_projects(
        name=name,
        start_date=start_date,
        end_date=end_date,
        page=page,
        size=size,
        status_files=status_files
    )
    log.info(f"Found {result.total} matching projects")
    return result


@router.get("/{project_id}", response_model=ProjectData)
async def get_project(project_id: int, service: ProjectService = Depends()) -> ProjectData:
    """Получить проекте по ID"""
    log.info(f"Getting project with id: {project_id}")
    result = await service.get_project(project_id)
    log.info(f"Found project: {result}")
    return result


@router.delete("/{project_id}")
async def delete_project(project_id: int, p_service: ProjectService = Depends(), f_service: FileService = Depends()):
    """Удалить проект по ID"""
    log.info(f"Deleting project and s3 folder with id: {project_id}")
    files = await f_service.get_project_files(project_id, to_delete=True)
    for file in files:
            await f_service.delete_file(file.id)
    await p_service.delete_project(project_id)
    log.info(f"Project {project_id} deleted")
    return {"status": "success"}


@router.put("/{project_id}", response_model=ProjectData)
async def update_project_name(
    project_id: int, project_data: CreateProjectData, service: ProjectService = Depends()
) -> ProjectData:
    """Изменить имя проекта"""
    log.info(f"Updating project {project_id} name to: {project_data.name}")
    result = await service.update_project_name(project_id, project_data.name)
    log.info(f"Project updated: {result}")
    return result


@router.get("/{project_id}/status", response_model=ProjectData)
async def update_project_status(project_id: int, service: ProjectService = Depends()) -> ProjectData:
    """Обновить статус проекта"""
    log.info(f"Updating project {project_id} status")
    result = await service.update_project_status(project_id)
    log.info(f"Project updated: {result}")
    return result


@router.post("/{project_id}", response_model=ProjectFileListData)
async def process_project_files(project_id: int, service: ProjectService = Depends()) -> ProjectFileListData:
    """Отправляет проект на обработку (можно использовать для повторной обработки)"""
    log.info(f"Started reprocessing project {project_id}")
    result = await service.process_project_files(project_id=project_id)
    log.info(f"Reprocessing project {project_id} completed!")
    return result