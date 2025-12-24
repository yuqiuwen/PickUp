import logging
import os
from logging.config import dictConfig, fileConfig
from pathlib import Path

from fastapi import Request, Response
from fastapi.routing import APIRoute

from app.config import settings


class AppLogger:
    @staticmethod
    def init(): 
        log_dir = settings.LOG_DIR
        log_dir.mkdir(parents=True, exist_ok=True)

        log_paths = {
            "error_log_path": str(log_dir / "error.log"),
            "access_log_path": str(log_dir / "access.log"),
            "job_log_path": str(log_dir / "job.log"),
        }

        # 获取配置文件路径
        config_dir = Path(__file__).parent.parent / "config"
        config_file = config_dir / "logging.ini"

        if not config_file.exists():
            raise FileNotFoundError(f"Logging config file not found: {config_file}")

        # 从ini文件加载配置，并传入日志文件路径参数
        fileConfig(str(config_file), defaults=log_paths, disable_existing_loggers=False)

    @staticmethod
    def get_app_logger():
        return logging.getLogger("app")


app_logger = AppLogger.get_app_logger()


class APIRouteLoggerHandler(APIRoute):
    def get_route_handler(self) -> callable:
        original_route_handler = super().get_route_handler()

        async def log_route_handler(request: Request) -> Response:
            # log_info = f"{request.client.host}:{request.client.port} - {request.method} {request.url.path} "
            # if request.query_params:
            #     log_info += f" | {request.query_params}"
            # app_logger.info(log_info)

            response: Response = await original_route_handler(request)

            # resp_log_info = f"response: {response.status_code} {request.url.path}"
            # app_logger.info(resp_log_info)
            return response

        return log_route_handler
