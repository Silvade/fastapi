import re

from pydantic import BaseModel, Field, field_validator, EmailStr


class User(BaseModel):
    name: str
    age: int


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
