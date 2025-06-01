from typing import Annotated

from pydantic import BaseModel, EmailStr, Field


class LoginData(BaseModel):
    email: EmailStr
    password: Annotated[str, Field(min_length=8, max_length=128)]