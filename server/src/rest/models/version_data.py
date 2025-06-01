from typing import Optional
from pydantic import BaseModel


class VersionData(BaseModel):
    component: Optional[str] = None
    branch: Optional[str] = None
    build_date: Optional[str] = None
    changeset: Optional[str] = None
