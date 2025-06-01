from datetime import datetime
from typing import List, Optional, Tuple
from sqlalchemy import Column, Integer, String, DateTime, Enum, select, delete, update
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

from dao.base import Base, with_async_db_session, session_factory
from dao.project_file import ProjectFile
from rest.models.project import ProjectData, ProjectStatusType, ProjectFilesStatusType

class Project(Base):
    __tablename__ = "projects"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, nullable=False)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    status = Column(Enum(ProjectStatusType, name="project_status_type"), nullable=False, default=ProjectStatusType.open)
    count_of_files = Column(Integer, nullable=False, default=0)
    status_files = Column(Enum(ProjectFilesStatusType, name="project_files_status_type"), nullable=False, default=ProjectFilesStatusType.processing)

    # Relationship with ProjectFile
    files = relationship("ProjectFile", back_populates="project", cascade="all, delete-orphan")

    def to_api(self) -> ProjectData:
        return ProjectData(
            id=self.id,
            name=self.name,
            created_at=self.created_at,
            status=self.status,
            count_of_files=self.count_of_files,
            status_files=self.status_files
        )

    @staticmethod
    @with_async_db_session
    async def create_project(name: str, status: ProjectStatusType) -> "Project":
        session = session_factory.get_async()
        project = Project(
            name=name,
            status=status
        )
        session.add(project)
        await session.commit()
        await session.refresh(project)
        return project

    @staticmethod
    @with_async_db_session
    async def search_projects(name: Optional[str] = None, status_files: Optional[str] = None,start_date: Optional[datetime] = None,
                              end_date: Optional[datetime] = None, page: int = 1, size: int = 20) -> Tuple[List["Project"], int]:
        session = session_factory.get_async()
        # Базовый запрос
        query = select(Project)
        # Добавляем фильтр по названию если указан
        if name:
            query = query.where(Project.name.ilike(f"%{name}%"))
        # Фильтр по статусу
        if status_files:
            query = query.where(Project.status_files == status_files)
        # Фильтр по дате создания
        if start_date:
            query = query.where(Project.created_at >= start_date)
        if end_date:
            query = query.where(Project.created_at <= end_date)
        # Получаем общее количество (с учетом фильтров)
        count_query = select(func.count()).select_from(query.subquery())
        total = await session.scalar(count_query)
        # Применяем пагинацию
        offset = (page - 1) * size
        paginated_query = query.order_by(Project.created_at.desc(), Project.id).offset(offset).limit(size)
        # Выполняем запрос
        result = await session.execute(paginated_query)
        projects = result.scalars().all()

        return projects, total

    @staticmethod
    @with_async_db_session
    async def get_project_by_id(project_id: int) -> Optional["Project"]:
        session = session_factory.get_async()
        query = select(Project).where(Project.id == project_id)
        result = await session.execute(query)
        return result.scalar_one_or_none()

    @staticmethod
    @with_async_db_session
    async def delete_project_by_id(project_id: int) -> None:
        session = session_factory.get_async()
        delete_query = delete(Project).where(Project.id == project_id)
        await session.execute(delete_query)
        await session.commit()

    @staticmethod
    @with_async_db_session
    async def update_project_name(project_id: int, new_name: str) -> Optional["Project"]:
        session = session_factory.get_async()

        # Update project name
        update_query = update(Project).where(Project.id == project_id).values(name=new_name)
        await session.execute(update_query)
        await session.commit()

        # Get updated project
        query = select(Project).where(Project.id == project_id)
        result = await session.execute(query)
        return result.scalar_one_or_none()

    @staticmethod
    @with_async_db_session
    async def update_project_status(project_id: int) -> Optional["Project"]:
        session = session_factory.get_async()

        # Получаем количество файлов
        file_count = await session.scalar(
            select(func.count())
            .select_from(ProjectFile)
            .where(ProjectFile.project_id == project_id)
        )

        # Получаем статистику по статусам файлов
        status_query = await session.execute(
            select(
                func.count().filter(ProjectFile.status == 'error').label('error_count'),
                func.count().filter(ProjectFile.status == 'processing').label('processing_count')
            ).where(ProjectFile.project_id == project_id)
        )

        # Извлекаем результаты запроса
        stats = status_query.first()

        # Определяем новый статус проекта
        if stats.error_count > 0:
            new_status = ProjectFilesStatusType.error
        elif stats.processing_count > 0:
            new_status = ProjectFilesStatusType.processing
        else:
            new_status = ProjectFilesStatusType.success

        # Обновляем проект
        await session.execute(
            update(Project)
            .where(Project.id == project_id)
            .values(
                count_of_files=file_count,
                status_files=new_status
            )
        )

        # Получаем обновленный проект
        result = await session.execute(
            select(Project)
            .where(Project.id == project_id)
        )

        await session.commit()
        return result.scalar_one_or_none()