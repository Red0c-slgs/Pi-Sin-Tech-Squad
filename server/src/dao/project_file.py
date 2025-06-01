from sqlalchemy import Column, Integer, String, ForeignKey, select, delete, Enum, update
from sqlalchemy.orm import relationship, selectinload
from sqlalchemy.sql import func
from typing import List, Optional, Tuple

from dao.base import Base, with_async_db_session, session_factory
from rest.models.project_file import ProjectFileData, ProjectFileStatusType, FileDefectData
from rest.models.panda_data import DefectType


class FileDefect(Base):
    __tablename__ = "file_defects"
    __table_args__ = {'extend_existing': True}

    id = Column(Integer, primary_key=True)
    file_id = Column(Integer, ForeignKey("project_files.id"), nullable=False)
    class_id = Column(Integer, nullable=False)  # ID класса дефекта из YOLO
    count = Column(Integer, default=1)  # Количество одинаковых дефектов

    # Связь с файлом
    file = relationship("ProjectFile", back_populates="defects")

    @classmethod
    @with_async_db_session
    async def create(cls, file_id: int, class_id: int, count: int = 1):
        session = session_factory.get_async()

        defect = cls(file_id=file_id, class_id=class_id, count=count)
        session.add(defect)
        await session.commit()
        await session.refresh(defect)
        return defect

    @classmethod
    @with_async_db_session
    async def delete_by_file(cls, file_id: int):
        session = session_factory.get_async()

        await session.execute(
            delete(cls).where(cls.file_id == file_id)
        )
        await session.commit()

    def to_api(self) -> FileDefectData:
        return FileDefectData(
            class_id=self.class_id,
            defect_name=DefectType.get_by_id(self.class_id).defect,
            count=self.count
        )


class ProjectFile(Base):
    __tablename__ = "project_files"

    id = Column(Integer, primary_key=True, autoincrement=True)
    project_id = Column(Integer, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    filename = Column(String, nullable=False)
    s3_path = Column(String, nullable=False)
    s3_url = Column(String, nullable=False)
    s3_icon_path = Column(String, nullable=False)
    s3_icon_url = Column(String, nullable=False)
    s3_txt_path = Column(String, nullable=False)
    s3_txt_url = Column(String, nullable=False)
    s3_report_path = Column(String, nullable=True)
    s3_report_url = Column(String, nullable=True)
    status = Column(Enum(ProjectFileStatusType, name="file_status_type"), nullable=False, default=ProjectFileStatusType.processing)

    project = relationship("Project", back_populates="files")

    defects = relationship("FileDefect", back_populates="file", cascade="all, delete-orphan", lazy='joined')
    defect_count = Column(Integer, default=0)  # Общее количество дефектов

    def to_api(self, label: str = "") -> ProjectFileData:
        return ProjectFileData(
            id=self.id,
            project_id=self.project_id,
            filename=self.filename,
            s3_path=self.s3_path,
            s3_url=self.s3_url,
            s3_icon_path=self.s3_icon_path,
            s3_icon_url=self.s3_icon_url,
            s3_txt_path=self.s3_txt_path,
            s3_txt_url=self.s3_txt_url,
            s3_report_path=self.s3_report_path or "",
            s3_report_url=self.s3_report_url or "",
            status=self.status,
            defects=[defect.to_api() for defect in self.defects] if self.defects else [],
            defect_count=self.defect_count,
            label=label
        )

    @staticmethod
    @with_async_db_session
    async def create_file(project_id: int, filename: str, s3_path: str, s3_url: str, s3_icon_path: str,
                          s3_icon_url: str, s3_txt_path: str = "", s3_txt_url: str = "") -> "ProjectFile":
        session = session_factory.get_async()
        project_file = ProjectFile(
            project_id=project_id,
            filename=filename,
            s3_path=s3_path,
            s3_url=s3_url,
            s3_icon_path=s3_icon_path,
            s3_icon_url=s3_icon_url,
            s3_txt_path=s3_txt_path,
            s3_txt_url=s3_txt_url,
        )
        session.add(project_file)
        await session.commit()
        await session.refresh(project_file)
        return project_file

    @staticmethod
    @with_async_db_session
    async def upload_txt(file_id: int, s3_txt_path: str, s3_txt_url: str):
        session = session_factory.get_async()

        update_query = update(ProjectFile).where(ProjectFile.id == file_id).values(s3_txt_path=s3_txt_path,
                                                                                   s3_txt_url=s3_txt_url)
        await session.execute(update_query)
        await session.commit()

        query = select(ProjectFile).options(selectinload(ProjectFile.defects)).where(ProjectFile.id == file_id)
        result = await session.execute(query)
        return result.scalar_one_or_none()

    @staticmethod
    @with_async_db_session
    async def get_file_by_id(file_id: int) -> Optional["ProjectFile"]:
        session = session_factory.get_async()
        query = select(ProjectFile).options(selectinload(ProjectFile.defects)).where(ProjectFile.id == file_id)
        result = await session.execute(query)
        return result.scalar_one_or_none()

    @staticmethod
    @with_async_db_session
    async def get_files_by_project_id(project_id: int, filename: Optional[str] = None, status: Optional[str] = None,
                                      defect_type: Optional[str] = None, min_defects: Optional[int] = None,
                                      max_defects: Optional[int] = None, page: int = 1, size: int = 20) -> Tuple[List["ProjectFile"], int]:
        session = session_factory.get_async()
        # Запрос для подсчета общего количества (без загрузки связанных данных)
        count_query = select(func.count(ProjectFile.id)).where(ProjectFile.project_id == project_id)

        # Фильтры для count_query
        if filename:
            count_query = count_query.where(ProjectFile.filename.ilike(f"%{filename}%"))
        if status:
            count_query = count_query.where(ProjectFile.status == status)
        if min_defects is not None:
            count_query = count_query.where(ProjectFile.defect_count >= min_defects)
        if max_defects is not None:
            count_query = count_query.where(ProjectFile.defect_count <= max_defects)

        # Выполняем запрос для подсчета
        total = await session.scalar(count_query)

        # Основной запрос с загрузкой связанных данных
        query = select(ProjectFile).options(selectinload(ProjectFile.defects)).where(
            ProjectFile.project_id == project_id)

        # Фильтры для основного запроса
        if filename:
            query = query.where(ProjectFile.filename.ilike(f"%{filename}%"))
        if status:
            query = query.where(ProjectFile.status == status)
        if defect_type is not None:
            query = query.join(FileDefect).where(FileDefect.class_id == defect_type)
        if min_defects is not None:
            query = query.where(ProjectFile.defect_count >= min_defects)
        if max_defects is not None:
            query = query.where(ProjectFile.defect_count <= max_defects)
        # Пагинация и сортировка
        query = query.order_by(ProjectFile.defect_count.desc())
        query = query.offset((page - 1) * size).limit(size)
        # Выполняем запрос
        result = await session.execute(query)
        projects = result.unique().scalars().all()

        return projects, total

    @staticmethod
    @with_async_db_session
    async def delete_file_by_id(file_id: int) -> None:
        session = session_factory.get_async()
        delete_query = delete(ProjectFile).where(ProjectFile.id == file_id)
        await session.execute(delete_query)
        await session.commit()


    @staticmethod
    @with_async_db_session
    async def update_file_status(file_id: int, status: ProjectFileStatusType) -> Optional["ProjectFile"]:
        """ Обновляет статус файла на указанный"""
        session = session_factory.get_async()

        # Обновляем файл
        await session.execute(update(ProjectFile).where(ProjectFile.id == file_id).values(status=status))

        # Получаем обновленный проект
        result = await session.execute(
            select(ProjectFile)
            .options(selectinload(ProjectFile.defects))
            .where(ProjectFile.id == file_id)
        )

        await session.commit()
        return result.scalar_one_or_none()

    @staticmethod
    @with_async_db_session
    async def delete_file_defects(file_id: int):
        """Удаляет все дефекты файла"""
        session = session_factory.get_async()
        await session.execute(delete(FileDefect).where(FileDefect.file_id == file_id))
        await session.commit()

    @staticmethod
    @with_async_db_session
    async def get_defect_stats(project_id: int) -> List[FileDefectData]:
        """Возвращает статистику по дефектам для проекта"""
        session = session_factory.get_async()
        query = (select(
            FileDefect.class_id,
            func.sum(FileDefect.count).label("total")
        ).join(ProjectFile).where(
            ProjectFile.project_id == project_id
        ).group_by(FileDefect.class_id))

        result = await session.execute(query)
        return [FileDefectData(class_id=class_id,
                               defect_name=DefectType.get_by_id(class_id).defect,
                               count=total)
                for class_id, total in result.all()]

    @classmethod
    @with_async_db_session
    async def update_defect_count(cls, file_id: int, count: int):
        session = session_factory.get_async()
        await session.execute(
            update(cls)
            .where(cls.id == file_id)
            .values(defect_count=count)
        )
        await session.commit()

    @staticmethod
    @with_async_db_session
    async def update_report_path(file_id: int, s3_report_path: str, s3_report_url: str) -> Optional["ProjectFile"]:
        """ Обновляет ссылки на отчеты .pdf"""
        session = session_factory.get_async()

        # Обновляем файл
        await session.execute(update(ProjectFile).where(ProjectFile.id == file_id).values(s3_report_path=s3_report_path,
                                                                                          s3_report_url=s3_report_url))

        # Получаем обновленный проект
        result = await session.execute(
            select(ProjectFile)
            .options(selectinload(ProjectFile.defects))
            .where(ProjectFile.id == file_id)
        )

        await session.commit()
        return result.scalar_one_or_none()