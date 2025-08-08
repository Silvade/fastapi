import uuid
import itsdangerous
from fastapi import FastAPI, Form, Cookie, HTTPException
from starlette.responses import Response

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

secret_key = "secret"
token_serializer = itsdangerous.URLSafeTimedSerializer(secret_key)
max_age = 120


@api.post("/login")
async def login(
    response: Response,
    username: str = Form(...),
    password: str = Form(...),
):
    if username in users_db and users_db[username]["password"] == password:
        id = str(uuid.uuid4())
        users_db[username]["id"] = id
        signature = token_serializer.dumps(id)
        response.set_cookie(
            key="session_token",
            value=signature,
            httponly=True,
            max_age=max_age,
        )
        return {"message": "куки установлены"}
    return {"message": "неверный логин или пароль"}


@api.get("/profile")
async def get_profile(session_token=Cookie()):
    try:
        unserialized_id = token_serializer.loads(session_token, max_age=max_age)
        user_ids = {users_db[x]["id"]: x for x in users_db}
        if unserialized_id in user_ids:
            return {"username": user_ids[unserialized_id]}
        raise HTTPException(status_code=401, detail="Unauthorized")
    except itsdangerous.BadSignature:
        return {"message": "Токен просрочен или неверный!"}
