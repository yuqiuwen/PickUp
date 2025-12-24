from contextlib import asynccontextmanager
import os
from pathlib import Path

from fastapi import APIRouter, FastAPI
from dotenv import load_dotenv
from starlette.middleware.sessions import SessionMiddleware

from app.config import settings
from app.ext import crypt
from app.core.http_handler import MsgSpecJSONResponse, register_exc_handler
from app.core.loggers import AppLogger, app_logger
from app.core.middleware import register_middleware
from app.core.register import lifespan, register_all
from app.routers import root_route, register_all_routes


def load_env(cfg_name):
    if cfg_name in ("production",):
        return

    env_dic = {
        "development": ".env",
        "testing": ".env.test",
        "unittest": ".env.unittest"
    }
    envfile = env_dic.get(cfg_name)
    env_path = str(Path(__file__).parent.parent / envfile)
    load_dotenv(dotenv_path=env_path, override=True)


def create_app(cfg_name) -> FastAPI:
    load_env(cfg_name)
    AppLogger.init()

    app = FastAPI(
        title=settings.APP_NAME,
        version=settings.FASTAPI_VERSION,
        summary=settings.FASTAPI_SUMMARY,
        docs_url=settings.FASTAPI_DOCS_URL,
        redoc_url=settings.FASTAPI_REDOC_URL,
        openapi_url=settings.FASTAPI_OPENAPI_URL,
        lifespan=lifespan,
        default_response_class=MsgSpecJSONResponse,
    )
    
    register_all(app)

    app_logger.info(f"Application initialized successfully in {cfg_name} environment")
    return app
