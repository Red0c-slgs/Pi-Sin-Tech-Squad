from pydantic import BaseModel, EmailStr


class UserResponseData(BaseModel):
    email: EmailStr
    name: str