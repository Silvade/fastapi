import secrets
import uuid
from datetime import datetime
from typing import Annotated
from passlib.context import CryptContext
import itsdangerous
from fastapi import (
    FastAPI,
    Form,
    Cookie,
    HTTPException,
    status,
    Response,
    Header,
    Depends,
)
from fastapi.security import HTTPBasic, HTTPBasicCredentials

from app.config import load_config
from app.models.models import (
    Feedback,
    FeedbackResponse,
    CommonHeaders,
    UserBase,
    User,
    UserInDB,
)

api = FastAPI()
# config = load_config()
# api.debug = config.debug

feedbacks = []


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


users_db = {"user123": "password123"}
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
async def old_login(
    response: Response,
    username: str = Form(...),
    password: str = Form(...),
):
    if username in users_db and users_db[username] == password:
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


def get_header_values(headers: CommonHeaders):
    return {
        "User-Agent": headers.user_agent,
        "Accept-Language": headers.accept_language,
    }


@api.get("/headers")
async def get_headers(headers: Annotated[CommonHeaders, Header()]):
    return get_header_values(headers)


@api.get("/info")
async def get_header_info(
    headers: Annotated[CommonHeaders, Header()], response: Response
):
    response.headers["X-Server-Time"] = datetime.now().isoformat()
    return {
        "message": "Добро пожаловать! Ваши заголовки успешно обработаны.",
        "headers": get_header_values(headers),
    }


auth_api = FastAPI()
security = HTTPBasic()
crypt_context = CryptContext(schemes=["bcrypt"])
fake_users_db: list[UserInDB] = []


def auth_user(credentials: HTTPBasicCredentials = Depends(security)):
    for user in fake_users_db:
        if secrets.compare_digest(user.username, credentials.username):
            if crypt_context.verify(credentials.password, user.hashed_password):
                return UserBase(username=credentials.username)
            else:
                break
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED, headers={"WWW-Authenticate": "Basic"}
    )


@auth_api.get("/login")
def login(user: UserBase = Depends(auth_user)):
    return {"message": f"Welcome, {user.username}!"}


@auth_api.post("/register")
def register_user(user: User):
    hashed_password = crypt_context.hash(user.password)
    user_data = UserInDB(username=user.username, hashed_password=hashed_password)
    fake_users_db.append(user_data)
    return {"message": f"Пользователь {user.username} успешно зарегистрирован."}
