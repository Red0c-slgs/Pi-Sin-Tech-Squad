from pydantic import BaseModel, Field
from typing import List
from enum import Enum


class YoloAnnotationData(BaseModel):
    content: str
    file_id: int


class ProjectFileStatusType(str, Enum):
    processing = "processing"
    success = "success"
    error = "error"
    process_error = "process_error"


class FileDefectData(BaseModel):
    class_id: int
    defect_name: str
    count: int


class ProjectFileData(BaseModel):
    id: int
    project_id: int
    filename: str
    s3_path: str
    s3_url: str
    s3_icon_path: str
    s3_icon_url: str
    s3_txt_path: str
    s3_txt_url: str
    s3_report_path: str = None
    s3_report_url: str = None
    status: ProjectFileStatusType
    defects: List[FileDefectData] = Field(default_factory=list)
    defect_count: int = 0
    label: str = None


class ProjectFileListData(BaseModel):
    items: List[ProjectFileData]
    total: int
    page: int
    size: int
    defect_statistics: List[FileDefectData] = Field(default_factory=list)
    total_defects: int = 0
