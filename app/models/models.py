import re

from pydantic import BaseModel, Field, field_validator, EmailStr


class User(BaseModel):
    name: str
    age: int


class Contact(BaseModel):
    email: EmailStr
    phone: int = Field(min_length=7, max_length=15)


class Feedback(BaseModel):
    name: str = Field(min_length=2, max_length=50)
    message: str = Field(min_length=10, max_length=500)
    contact: Contact

    @field_validator("message")
    def check_message(cls, value):
        if re.search(r"(редиск|бяк|козявк)(а|и|у|е|ой)", value):
            raise ValueError("Использование недопустимых слов")
        return value


class FeedbackResponse(BaseModel):
    message: str
