from pydantic import BaseModel, EmailStr, Field, ConfigDict
from datetime import date
from typing import Optional

from src.database.models import Role


class ContactModel(BaseModel):
    name: str = Field(max_length=50)
    surname: str = Field(max_length=50)
    email: EmailStr
    phone_number: str = Field(max_length=25)
    birthday: Optional[date] = None
    additional_info: Optional[str] = None


class ContactResponse(ContactModel):
    id: int
    model_config = ConfigDict(from_attributes=True)


class ContactUpdate(BaseModel):
    name: Optional[str] = None
    surname: Optional[str] = None
    email: Optional[EmailStr] = None
    phone_number: Optional[str] = None
    birthday: Optional[date] = None
    additional_info: Optional[str] = None


class BirthdaysResponse(BaseModel):
    message: str
    contacts: list[ContactResponse] = []


class UserModel(BaseModel):
    id: int
    username: str
    email: str
    avatar: str

    model_config = ConfigDict(from_attributes=True)


class UserCreate(BaseModel):
    username: str
    email: str
    password: str


class TokenModel(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str


class TokenRefreshRequest(BaseModel):
    refresh_token: str


class RequestEmail(BaseModel):
    email: EmailStr


class ForgotPasswordBody(BaseModel):
    email: EmailStr

class ResetPasswordBody(BaseModel):
    token: str
    new_password: str