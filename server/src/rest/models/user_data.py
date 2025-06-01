from typing import Annotated

from pydantic import BaseModel, EmailStr, Field


class UserData(BaseModel):
    email: EmailStr
    name: Annotated[str, Field(min_length=4, max_length=128)]
    password: Annotated[str, Field(min_length=8, max_length=128)]

