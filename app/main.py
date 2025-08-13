import re
import uuid
from datetime import datetime

import itsdangerous
from fastapi import FastAPI, Form, Cookie, HTTPException, status, Response, Header

from app.config import load_config
from app.models.models import Feedback, User, FeedbackResponse, UserCreate

api = FastAPI()
# config = load_config()
# api.debug = config.debug

feedbacks = []


def is_adult(age: int):
    return age >= 18


@api.post("/user")
async def add_user_field(user_info: User):
    result = dict(user_info)
    result["is_adult"] = is_adult(user_info.age)
    return result


@api.post("/create_user", response_model=UserCreate)
async def create_user(user_info: UserCreate):
    return user_info


@api.post("/feedback")
async def send_feedback(feedback: Feedback, is_premium: bool | None = False):
    feedbacks.append(feedback)
    response = f"Спасибо, {feedback.name}! Ваш отзыв сохранён."
    if is_premium:
        response += " Ваш отзыв будет рассмотрен в приоритетном порядке."
    return FeedbackResponse(message=response)


sample_product_1 = {
    "product_id": 123,
    "name": "Smartphone",
    "category": "Electronics",
    "price": 599.99,
}

sample_product_2 = {
    "product_id": 456,
    "name": "Phone Case",
    "category": "Accessories",
    "price": 19.99,
}

sample_product_3 = {
    "product_id": 789,
    "name": "Iphone",
    "category": "Electronics",
    "price": 1299.99,
}

sample_product_4 = {
    "product_id": 101,
    "name": "Headphones",
    "category": "Accessories",
    "price": 99.99,
}

sample_product_5 = {
    "product_id": 202,
    "name": "Smartwatch",
    "category": "Electronics",
    "price": 299.99,
}

sample_products = [
    sample_product_1,
    sample_product_2,
    sample_product_3,
    sample_product_4,
    sample_product_5,
]

sample_products_dict = {product["product_id"]: product for product in sample_products}


@api.get("/product/{product_id}")
async def get_product_info(product_id: int):
    return sample_products_dict[product_id]


@api.get("/products/search")
async def get_product_info(
    keyword: str, category: str | None = None, limit: int | None = 10
):
    filtered_products = filter(lambda x: keyword in x["name"], sample_products)
    if category:
        filtered_products = filter(
            lambda x: x["category"] == category, filtered_products
        )
    return list(filtered_products)[:limit]


users_db = {"user123": {"password": "password123"}}
user_ids_db = {}
secret_key = "secret"
token_serializer = itsdangerous.URLSafeTimedSerializer(secret_key)
max_age = 360


def update_cookie_time(response: Response, id):
    signature = token_serializer.dumps(id)
    response.set_cookie(
        key="session_token",
        value=signature,
        httponly=True,
        secure=False,
        max_age=max_age,
    )


@api.post("/login")
async def login(
    response: Response,
    username: str = Form(...),
    password: str = Form(...),
):
    if username in users_db and users_db[username]["password"] == password:
        id = str(uuid.uuid4())
        user_ids_db[id] = username
        update_cookie_time(response, id)
        return {"message": "куки установлены"}
    return {"message": "неверный логин или пароль"}


@api.get("/profile")
async def get_profile(response: Response, session_token=Cookie()):
    try:
        unserialized_id, timestamp = token_serializer.loads(
            session_token, max_age=max_age, return_timestamp=True
        )
        if unserialized_id in user_ids_db:
            print(timestamp.timestamp())
            past_time = datetime.now().timestamp() - timestamp.timestamp()
            if past_time > 5 * 60:
                raise HTTPException(
                    status_code=401, detail={"message": "Session expired"}
                )
            elif past_time > 3 * 60:
                update_cookie_time(response, unserialized_id)
            return {"username": user_ids_db[unserialized_id]}
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"message": "Invalid session"},
        )
    except itsdangerous.BadSignature:
        raise HTTPException(status_code=401, detail={"message": "Invalid session"})


@api.get("/headers")
async def get_headers(
    user_agent: str = Header(None), accept_language: str = Header(None)
):
    if user_agent is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Header `user_agent` is empty",
        )
    if accept_language is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Header `accept_language` is empty",
        )
    languages = accept_language.split(",")
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
    return {"User-Agent": user_agent, "Accept-Language": accept_language}
