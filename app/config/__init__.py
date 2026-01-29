import importlib
import os
import platform
import logging
from functools import lru_cache

from typing import Literal, Pattern
from zoneinfo import ZoneInfo
from pathlib import Path
from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


T_ENV = Literal["development", "testing", "production", "unittest"]


def load_config_class():
    config_name = os.getenv("APP_ENV", "development")
    cfg_class_name = f"{config_name.capitalize()}Config"
    config_class = getattr(importlib.import_module("app.config"), cfg_class_name)
    return config_class()


class Settings(BaseSettings):
    model_config = SettingsConfigDict(extra="ignore", env_file_encoding="utf-8")

    @field_validator("API_KEYS", mode="before")
    def parse_api_keys(cls, v):
        if isinstance(v, str):
            return {key.strip() for key in v.split(",")}
        return None

    # FastAPI
    FASTAPI_API_V1_PATH: str = "/v1"
    FASTAPI_TITLE: str = "内容制作系统"
    FASTAPI_VERSION: str = "0.1.0"
    FASTAPI_SUMMARY: str = "内容制作系统"
    FASTAPI_DESCRIPTION: str = ""
    FASTAPI_DOCS_URL: str = "/docs"
    FASTAPI_REDOC_URL: str = "/redoc"
    FASTAPI_OPENAPI_URL: str | None = "/openapi.json"

    # CORS
    CORS_ALLOWED_ORIGINS: list[str] = []

    # 白名单路由列表
    WHITE_ROUTE_LIST: set[str] = {
        "/docs",
        "/redoc",
        "/openapi.json",
    }

    # 白名单路由正则
    WHITE_ROUTE_PATTERN: set[Pattern[str]] = set()

    APP_NAME: str = os.getenv("APP_NAME", "fast_app").lower()
    ENV: T_ENV = os.getenv("APP_ENV", "development")
    TESTING: bool = False
    TIMEZONE: ZoneInfo = ZoneInfo("Asia/Shanghai")
    ENABLE_REQ_LOG: bool = True
    AUTH_SECRET_KEY: str | None = os.getenv("AUTH_SECRET_KEY")  # secrets.token_urlsafe(32)

    BASE_DIR: Path = Path(__file__).resolve().parent.parent.parent
    STATIC_DIR: Path = Path(f"/data/resource/{APP_NAME}")
    LOG_DIR: Path = Path(f"/data/logs/{APP_NAME}")

    if platform.system() in ("Darwin", "Windows"):
        home: Path = Path.home()
        STATIC_DIR: Path = home / "data" / "resource" / APP_NAME
        LOG_DIR: Path = home / "data" / "logs" / APP_NAME

    TOKEN_EXPIRES: int = 60 * 60 * 24 * 3
    TOKEN_REFRESH_EXPIRE: int = 60 * 60 * 24 * 15
    TOKEN_SECRET_KEY: str = os.getenv("TOKEN_SECRET_KEY")  # secrets.token_urlsafe(32)
    COOKIE_REFRESH_TOKEN_KEY: str = "refresh_token"
    TOKEN_ALGORITHM: str = "HS256"
    INVITE_TOKEN_SECRET: str = os.getenv("INVITE_TOKEN_SECRET")

    API_KEYS: set[str] | None = None

    ENABLE_SOCKET: bool = False  # 是否启用socket

    # DB
    SQLALCHEMY_ECHO: bool = False
    DB_MAIN_URL: str | None = os.getenv("DB_MAIN_URL")

    # Redis
    REDIS_TIMEOUT: int = 5
    REDIS_CACHE_URL: str | None = os.getenv("REDIS_CACHE_URL")
    REDIS_LOCK_URL: str | None = os.getenv("REDIS_LOCK_URL")
    REDIS_PMS_URL: str | None = os.getenv("REDIS_PMS_URL")
    REDIS_LIMITER_URL: str | None = os.getenv("REDIS_LIMITER_URL")
    REDIS_SOCKET_URL: str | None = os.getenv("REDIS_SOCKET_URL")

    # Email Service Configuration
    EMAIL_SMTP_SERVER: str = os.getenv("EMAIL_SMTP_SERVER")
    EMAIL_SMTP_PORT: int = int(os.getenv("EMAIL_SMTP_PORT", 0))
    EMAIL_SENDER: str | None = os.getenv("EMAIL_SENDER")
    EMAIL_PASSWORD: str | None = os.getenv("EMAIL_PASSWORD")

    # 免授权直连
    WS_NO_AUTH_MARKER: str = "internal"
    TOKEN_ONLINE_REDIS_PREFIX: str = f"{APP_NAME}:token_online"
    SID_MAP_KEY: str = f"{APP_NAME}:sid_map"

    # Celery
    CELERY_BROKER_URL: str | None = os.getenv("CELERY_BROKER_URL")
    CELERY_RESULT_BACKEND: str | None = os.getenv("CELERY_RESULT_BACKEND")
    CELERY_TIMEZONE: str = "Asia/Shanghai"
    CELERY_ENABLE_UTC: bool = True
    # 任务执行时将报告其状态为“已启动”, 当存在长时间运行的任务且需要报告当前正在执行的任务时，“已启动”状态会很有用。
    CELERY_TASK_TRACK_STARTED: bool = True
    CELERY_TASK_ACKS_LATE: bool = True  # 延迟确认（任务完成之后再确认）
    CELERY_TASK_ALWAYS_EAGER: bool = False
    CELERYBEAT_SCHEDULE_FILENAME: Path = STATIC_DIR / "celerybeat-schedule"
    CELERY_TASK_REJECT_ON_WORKER_LOST: bool = True  # 设为True, worker进程崩掉之后将重新加入worker
    CELERY_WORKER_SEND_TASK_EVENTS: bool = True  # 发送任务相关的事件，便于flower等监控

    WEB_BASE_URL: str = os.getenv("WEB_BASE_URL")
    EMAIL_ACCEPT_URL: str = os.getenv("EMAIL_ACCEPT_URL")
    EMAIL_DECLINE_URL: str = os.getenv("EMAIL_ACCEPT_URL")
    SIGNUP_SITE_URL: str = WEB_BASE_URL + os.getenv("SIGNUP_URL")


class DevelopmentConfig(Settings):
    model_config = SettingsConfigDict(
        env_file=".env", env_ignore_empty=True, env_file_encoding="utf-8"
    )

    SQLALCHEMY_ECHO: bool = True
    DEBUG: bool = True
    LOG_LEVEL: int = logging.DEBUG
    ENABLE_REQ_LOG: bool = False

    DB_MAIN_TEST_URL: str | None = os.getenv("DB_MAIN_TEST_URL")

    # 本地自测，同步执行
    CELERY_TASK_ALWAYS_EAGER: bool = False


class TestingConfig(Settings):
    model_config = SettingsConfigDict(
        env_file=".env.test", env_ignore_empty=True, env_file_encoding="utf-8"
    )

    TESTING: bool = True
    LOG_LEVEL: int = logging.INFO
    SMS_URL: str | None = None

    DB_MAIN_TEST_URL: str | None = os.getenv("DB_MAIN_TEST_URL")


class UnittestConfig(Settings):
    model_config = SettingsConfigDict(
        env_file=".env.unittest", env_ignore_empty=True, env_file_encoding="utf-8"
    )

    DB_MAIN_TEST_URL: str | None = os.getenv("DB_MAIN_TEST_URL")


class ProductionConfig(Settings):
    model_config = SettingsConfigDict(env_ignore_empty=True, env_file_encoding="utf-8")

    FASTAPI_DOCS_URL: str | None = None
    FASTAPI_REDOC_URL: str | None = None
    FASTAPI_OPENAPI_URL: str | None = None

    LOG_LEVEL: int = logging.INFO
    SMS_URL: str | None = None


@lru_cache()
def get_settings() -> DevelopmentConfig | TestingConfig | UnittestConfig | ProductionConfig:
    return load_config_class()


settings = get_settings()
