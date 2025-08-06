from fastapi import FastAPI

from app.config import load_config
from app.models.models import Feedback, User, FeedbackResponse

api = FastAPI()
# config = load_config()
# api.debug = config.debug

feedbacks = []


def is_adult(age: int):
    return age >= 18

#
# @api.post("/user")
# async def add_user_field(user_info: User):
#     result = dict(user_info)
#     result["is_adult"] = is_adult(user_info.age)
#     return result


@api.post("/feedback")
async def send_feedback(feedback: Feedback, is_premium: bool | None = False):
    feedbacks.append(feedback)
    response = f"Спасибо, {feedback.name}! Ваш отзыв сохранён."
    if is_premium:
        response += " Ваш отзыв будет рассмотрен в приоритетном порядке."
    return FeedbackResponse(message=response)
