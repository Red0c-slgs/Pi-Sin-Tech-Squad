from pydantic import BaseModel
from typing import Optional


class LoginResponse(BaseModel):
    message: str
    token: Optional[str] = None
    account_id: Optional[int] = None