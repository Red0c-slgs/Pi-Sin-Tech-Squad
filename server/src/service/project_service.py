from typing import Optional
from fastapi import HTTPException

from dao.base import with_async_db_session
from dao.project import Project
from rest.models.project import ProjectData, ProjectListData, CreateProjectData, ProjectStatusType
from rest.models.project_file import ProjectFileListData, ProjectFileData
from service.file_service import FileService
from utils.logger import get_logger

from datetime import datetime

log = get_logger("ProjectService")


class ProjectService:

    def __init__(self):
        self.file_service = FileService()

    @with_async_db_session
    async def create_project(self, project_data: CreateProjectData) -> ProjectData:
        log.info(f"Creating project: {project_data.name}")
        project = await Project.create_project(project_data.name, ProjectStatusType.open)
        return project.to_api()

    @with_async_db_session
    async def search_projects(self, name: Optional[str] = None, status_files: Optional[str] = None, start_date: Optional[datetime] = None,
                              end_date: Optional[datetime] = None, page: int = 1, size: int = 20) -> ProjectListData:
        log.info(f"Getting projects, filters: name={name}, date_range={start_date}-{end_date}")

        projects, total = await Project.search_projects(name=name, start_date=start_date,
                                                        end_date=end_date, page=page, size=size,
                                                        status_files=status_files,)

        items = [project.to_api() for project in projects]

        return ProjectListData(
            items=items,
            total=total,
            page=page,
            size=size
        )

    @with_async_db_session
    async def get_project(self, project_id: int) -> ProjectData:
        log.info(f"Getting project with id: {project_id}")
        
        project = await Project.get_project_by_id(project_id)
        
        if not project:
            raise ValueError(f"Project with id {project_id} not found")
        
        return project.to_api()

    @with_async_db_session
    async def delete_project(self, project_id: int) -> None:
        log.info(f"Deleting project with id: {project_id}")
        
        # Check if project exists
        project = await Project.get_project_by_id(project_id)
        
        if not project:
            raise ValueError(f"Project with id {project_id} not found")
        
        # Delete project
        await Project.delete_project_by_id(project_id)

    @with_async_db_session
    async def update_project_name(self, project_id: int, new_name: str) -> ProjectData:
        log.info(f"Updating project {project_id} name to: {new_name}")
        
        # Check if project exists
        project = await Project.get_project_by_id(project_id)
        
        if not project:
            raise ValueError(f"Project with id {project_id} not found")
        
        # Update project name
        updated_project = await Project.update_project_name(project_id, new_name)
        
        if not updated_project:
            raise ValueError(f"Failed to update project with id {project_id}")
        
        return updated_project.to_api()

    @with_async_db_session
    async def update_project_status(self, project_id: int):
        log.info(f"Updating project {project_id} status")

        # Check if project exists
        project = await Project.get_project_by_id(project_id)

        if not project:
            raise ValueError(f"Project with id {project_id} not found")

        # Update project status
        updated_project = await Project.update_project_status(project_id)

        if not updated_project:
            raise ValueError(f"Failed to update project with id {project_id}")

        return updated_project.to_api()

    @with_async_db_session
    async def process_project_files(self, project_id: int, page: int = 1, size: int = 20) -> ProjectFileListData:
        """
        Отправляет все файлы проекта на обработку и возвращает ProjectFileListData
        """
        log.info(f"Processing all files for project {project_id}")

        # 1. Проверяем существование проекта
        project = await Project.get_project_by_id(project_id)
        if not project:
            log.error(f"Project {project_id} not found")
            raise HTTPException(status_code=404, detail="Project not found")

        # 2. Получаем все файлы проекта в формате ProjectFileListData
        files_data: ProjectFileListData = await self.file_service.get_project_files(project_id=project_id, page=page,
                                                                                    size=size, to_delete=False)

        if not files_data.items:
            log.info(f"No files found for project {project_id}")
            return ProjectFileListData(items=[], total=0, page=page, size=size)

        # 3. Обновляем статус проекта
        await Project.update_project_status(project_id=project_id)

        # 4. Отправляем каждый файл на обработку
        processed_files = []
        for file in files_data.items:
            try:
                # Проверяем, что файл еще не в обработке
                # if file.status != "processing":
                processed_file = await self.file_service.process_file(file.id)
                processed_files.append(processed_file)
                # else:
                #     log.info(f"File {file.id} is already being processed")
                #     processed_files.append(file)
            except Exception as e:
                log.error(f"Error processing file {file.id}: {str(e)}")
                # Создаем объект с ошибкой для включения в результат
                error_file = ProjectFileData(
                    id=file.id,
                    project_id=file.project_id,
                    filename=file.filename,
                    s3_path=file.s3_path,
                    s3_url=file.s3_url,
                    s3_icon_path=file.s3_icon_path,
                    s3_icon_url=file.s3_icon_url,
                    s3_txt_path=file.s3_txt_path,
                    s3_txt_url=file.s3_txt_url,
                    status="process_error"
                )
                processed_files.append(error_file)

        # 5. Обновляем статус проекта после отправки
        await self.update_project_status(project_id)

        # Получаем результат
        result = await FileService.get_project_files(project_id=project_id, page=page, size=size, to_delete=False)
        return result
