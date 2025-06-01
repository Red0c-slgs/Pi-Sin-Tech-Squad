from datetime import datetime
from enum import Enum
from typing import List, Optional
from pydantic import BaseModel


class S3LinkData(BaseModel):
    url: str
    status: str


class ProjectStatusType(str, Enum):
    open = "open"
    close = "close"


class ProjectFilesStatusType(str, Enum):
    processing = "processing"
    success = "success"
    error = "error"


class ProjectData(BaseModel):
    id: Optional[int] = None
    name: str
    created_at: datetime = None
    status: ProjectStatusType
    count_of_files: int
    status_files: ProjectFilesStatusType


class CreateProjectData(BaseModel):
    name: str


class ProjectListData(BaseModel):
    items: List[ProjectData]
    total: int
    page: int
    size: int
