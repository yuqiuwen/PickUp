#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import importlib
import pkgutil

from fastapi import APIRouter

from app.core.loggers import APIRouteLoggerHandler
from app.config import settings


class BaseAPIRouter(APIRouter):
    def __init__(
        self,
        *args,
        enable_req_log=settings.ENABLE_REQ_LOG,
        response_model_exclude_none=True,
        **kwargs,
    ):
        super().__init__(*args, **kwargs)
        self.response_model_exclude_none = response_model_exclude_none
        if enable_req_log:
            self.route_class = APIRouteLoggerHandler

    def add_api_route(self, path: str, endpoint, **kwargs):
        kwargs.update(response_model_exclude_none=self.response_model_exclude_none)
        return super().add_api_route(path, endpoint, **kwargs)


root_route = APIRouter()


def register_all_routes(app):
    pkg = importlib.import_module("app.routers")
    pkg_name = pkg.__name__
    router_name = "router"
    for _, name, is_pkg in pkgutil.iter_modules(pkg.__path__, prefix=pkg_name + "."):
        if not is_pkg:
            continue

        version_modules = importlib.import_module(name)
        api_prefix = getattr(version_modules, "API_PREFIX", name.split(".")[-1])

        for _, submodule_name, _ in pkgutil.iter_modules(
            version_modules.__path__, prefix=name + "."
        ):
            submodule = __import__(submodule_name, fromlist=(router_name,))
            if hasattr(submodule, router_name):
                root_route.include_router(submodule.router, prefix="/" + api_prefix)

    app.include_router(root_route)
