from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi.exceptions import RequestValidationError
from fastapi import FastAPI
from slowapi.errors import RateLimitExceeded
import socketio
from starlette.middleware.authentication import AuthenticationMiddleware
from fastapi.openapi.utils import get_openapi

from app.config import settings
from app.core.exception import APIException, AuthException, DecryptedError, ValidateError
from app.core.http_handler import make_response, register_exc_handler
from app.core.loggers import app_logger
from app.core.middleware import register_middleware
from app.database.db import init_async_engine_and_session
from app.ext import crypt
from app.database import redis_client
from app.middlewares.jwt_auth import JwtAuthMiddleware
from app.routers import register_all_routes


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """
    启动初始化

    :param app: FastAPI 应用实例
    :return:
    """
    init_async_engine_and_session(settings.DB_MAIN_URL)
    await redis_client.init(enable_redis_socket=settings.ENABLE_SOCKET)

    yield

    await redis_client.aclose()


def register_route(app: FastAPI) -> None:
    register_all_routes(app)


def register_ext(app: FastAPI) -> None:
    crypt.init_key()


def register_socket_app(app: FastAPI) -> None:
    """
    注册 Socket.IO 应用

    :param app: FastAPI 应用实例
    :return:
    """
    from app.common.socketio.server import sio

    socket_app = socketio.ASGIApp(
        socketio_server=sio,
        other_asgi_app=app,
        socketio_path="/ws/socket.io",
    )
    app.mount("/ws", socket_app)


def custom_openapi(app: FastAPI):
    if app.openapi_schema:
        return app.openapi_schema

    openapi_schema = get_openapi(
        title=app.title,
        version=app.version,
        description=app.description,
        routes=app.routes,
    )
    # 定义一个 HTTP Bearer 安全方案
    openapi_schema.setdefault("components", {})
    openapi_schema["components"].setdefault("securitySchemes", {})
    openapi_schema["components"]["securitySchemes"]["BearerAuth"] = {
        "type": "http",
        "scheme": "bearer",
        "bearerFormat": "JWT",  # 可写可不写，只是说明
    }

    # 默认对所有接口应用这个 security（相当于全局需要认证）
    openapi_schema["security"] = [{"BearerAuth": []}]

    return openapi_schema


def register_all(app: FastAPI):
    register_route(app)
    register_ext(app)
    app.add_middleware(
        AuthenticationMiddleware,
        backend=JwtAuthMiddleware(),
        on_error=JwtAuthMiddleware.auth_exception_handler,
    )
    app.openapi_schema = custom_openapi(app)
    register_middleware(app)
    register_exc_handler(app)

    if settings.ENABLE_SOCKET:
        register_socket_app(app)
