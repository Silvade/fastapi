import re

from pydantic import BaseModel, Field, field_validator


class User(BaseModel):
    name: str
    age: int


class Feedback(BaseModel):
    name: str = Field(min_length=2, max_length=50)
    message: str = Field(min_length=10, max_length=500)

    @field_validator("message")
    def check_message(cls, value):
        return re.match(r"(редиск|бяк|козявк)(а|и|у|е|ой)")
