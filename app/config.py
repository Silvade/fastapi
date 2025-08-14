from dataclasses import dataclass
from enum import StrEnum
from environs import Env


@dataclass
class DatabaseConfig:
    database_url: str


class Mode(StrEnum):
    DEV = "DEV"
    PROD = "PROD"


@dataclass
class Config:
    db: DatabaseConfig
    secret_key: str
    debug: bool
    mode: Mode
    docs_user: str | None = None
    docs_password: str | None = None


def load_config(path: str = None) -> Config:
    env = Env()
    env.read_env(path)
    if env("MODE") not in Mode:
        raise ValueError("Переменная окружения MODE имеет недопустимое значение.")

    return Config(
        db=DatabaseConfig(database_url=env("DATABASE_URL")),
        secret_key=env("SECRET_KEY"),
        debug=env.bool("DEBUG", default=False),
        mode=env("MODE"),
        docs_user=env("DOCS_USER"),
        docs_password=env("DOCS_PASSWORD"),
    )
