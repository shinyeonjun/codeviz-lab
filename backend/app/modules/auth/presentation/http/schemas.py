from datetime import datetime

from pydantic import BaseModel, Field


class AuthUserRead(BaseModel):
    id: str
    email: str
    name: str
    created_at: datetime = Field(serialization_alias="createdAt")


class AuthSessionRead(BaseModel):
    is_authenticated: bool = Field(serialization_alias="isAuthenticated")
    user: AuthUserRead | None = None


class RegisterCreate(BaseModel):
    email: str = Field(min_length=3, max_length=255)
    password: str = Field(min_length=8, max_length=128)
    name: str = Field(min_length=1, max_length=100)


class LoginCreate(BaseModel):
    email: str = Field(min_length=3, max_length=255)
    password: str = Field(min_length=8, max_length=128)
