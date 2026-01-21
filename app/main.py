from pathlib import Path

from fastapi import FastAPI
from dotenv import load_dotenv

from app.core.http_handler import MsgSpecJSONResponse
from app.core.loggers import AppLogger, app_logger
from app.core.register import lifespan, register_all


def create_app(cfg_name) -> FastAPI:
    from app.config import settings

    AppLogger.init()
    app = FastAPI(
        title=settings.APP_NAME,
        version=settings.FASTAPI_VERSION,
        summary=settings.FASTAPI_SUMMARY,
        docs_url=settings.FASTAPI_DOCS_URL,
        redoc_url=settings.FASTAPI_REDOC_URL,
        openapi_url=settings.FASTAPI_OPENAPI_URL,
        swagger_ui_parameters={"persistAuthorization": True},
        lifespan=lifespan,
        default_response_class=MsgSpecJSONResponse,
    )

    register_all(app)

    app_logger.info(f"Application initialized successfully in {cfg_name} environment")
    return app
