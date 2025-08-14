import re

from fastapi import HTTPException, status
from pydantic import BaseModel, Field, field_validator, EmailStr

MINIMUM_APP_VERSION = "1.5.5"


class UserCreate(BaseModel):
    name: str
    email: EmailStr
    age: int | None = Field(None, gt=0)
    is_subscribed: bool | None = None


class Contact(BaseModel):
    email: EmailStr
    phone: int | None = Field(None, gt=999999, lt=1000000000000000)


class Feedback(BaseModel):
    contact: Contact
    name: str = Field(min_length=2, max_length=50)
    message: str = Field(min_length=10, max_length=500)

    @field_validator("message")
    def check_message(cls, value):
        if re.search(r"(редиск|бяк|козявк)(а|и|у|е|ой)", value):
            raise ValueError("Использование недопустимых слов")
        return value


class FeedbackResponse(BaseModel):
    message: str


class CommonHeaders(BaseModel):
    user_agent: str
    accept_language: str
    x_current_version: str = Field(pattern=r"^\d\.\d\.\d$")

    @field_validator("accept_language")
    def check_accept_language_format(cls, value):
        languages = value.split(",")
        for language in languages:
            separator = ";"
            if separator in language:
                left, right = map(str.strip, language.split(separator))
            else:
                left = language.strip()
                right = None
            if not re.fullmatch(r"\*|[a-z]{2}|[a-z]{2}-[A-Z]{2}", left) or (
                right is not None and not re.fullmatch(r"q=\d.\d", right)
            ):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Header `accept_language` has incorrect format",
                )
        return value

    @field_validator("x_current_version")
    def check_x_current_version(cls, value):
        if value < MINIMUM_APP_VERSION:
            raise ValueError("Требуется обновить приложение")


class UserBase(BaseModel):
    username: str


class User(UserBase):
    password: str


class UserInDB(UserBase):
    hashed_password: str
