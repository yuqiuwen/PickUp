from typing import Any, Generic, TypeVar
from fastapi.responses import JSONResponse, ujson
from fastapi.exceptions import RequestValidationError
from pydantic import BaseModel, ConfigDict, model_serializer
from pydantic.functional_serializers import PlainSerializer
from slowapi.errors import RateLimitExceeded
from msgspec import json as msgspec_json

from app.core.exception import (
    APIException,
    AuthException,
    DecryptedError,
    PermissionDenied,
    ValidateError,
)
from app.core.loggers import app_logger
from app.utils.paginator import CursorPaginatedResponse, PaginatedResponse


T = TypeVar("T")


class RespModel(BaseModel, Generic[T]):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    code: int = 0
    msg: str = "successful"
    data: T | None = None
    errmsg: str | None = None

    # @model_serializer(mode='wrap')
    # def serialize(self, serializer):
    #     # TODO 先让 Pydantic 序列化所有字段（包括泛型类型）
    #     result = serializer(self)
    #     if self.data is not None:
    #         result["data"] = self.data
    #     if self.errmsg is not None:
    #         result["errmsg"] = self.errmsg

    #     return {k: v for k, v in result.items() if v is not None}


class PageRespModel(RespModel[PaginatedResponse[T]], Generic[T]):
    """统一分页响应：外层 RespModel，data 里是 PaginatedResponse[T]"""

    pass


class CursorPageRespModel(RespModel[CursorPaginatedResponse[T]], Generic[T]):
    """统一游标分页响应：外层 RespModel，data 里是 CursorPaginatedResponse[T]"""

    pass


class MsgSpecJSONResponse(JSONResponse):
    """
    使用高性能的 msgspec 库将数据序列化为 JSON 的响应类
    """

    def render(self, content: Any) -> bytes:
        return msgspec_json.encode(content)


def _build_resp_body(code: int, msg: str, data: Any = None, errmsg: str | None = None) -> dict:
    ret = {"code": code, "msg": msg}

    if data is not None:
        ret["data"] = data
    if errmsg is not None:
        ret["errmsg"] = errmsg
    return ret


def make_response(
    msg="successful", *, data: Any | BaseModel = None, code=0, errmsg=None
) -> RespModel:
    resp = RespModel(
        code=code,
        msg=msg,
        errmsg=errmsg,
        data=data,
    )
    return resp


def make_json_response(msg="successful", *, data: Any = None, code=0, errmsg=None):
    data = _build_resp_body(code, msg, data, errmsg)
    return JSONResponse(data, media_type="application/json; charset=utf-8")


def make_fast_response(msg="successful", *, data: Any = None, code=0, errmsg=None):
    data = _build_resp_body(code, msg, data, errmsg)
    return MsgSpecJSONResponse(data)


def register_exc_handler(app):
    default_msg = "系统出错啦~"
    default_code = 500

    # 通用的 Exception
    @app.exception_handler(Exception)
    def custom_exc_handler(request, exc: Exception):
        app_logger.error(str(exc))
        return make_json_response("Server Error!", code=default_code, errmsg=default_msg)

    # 具体的异常处理器要先注册，通用的 Exception 处理器放在最后
    @app.exception_handler(APIException)
    def server_exc_handler(request, exc: APIException):
        return make_json_response(exc.message or "Server Error!", code=exc.code, errmsg=exc.errmsg)

    @app.exception_handler(RequestValidationError)
    async def req_validation_exc_handler(request, exc: RequestValidationError):
        app_logger.warning(str(exc.args))
        return make_json_response("parameters error", code=400, errmsg="参数错误")

    @app.exception_handler(ValidateError)
    async def validation_exc_handler(request, exc: ValidateError):
        app_logger.warning(str(exc))
        return make_json_response("parameters error", code=422, errmsg=exc.errmsg)

    @app.exception_handler(AuthException)
    async def auth_exc_handler(request, exc: AuthException):
        return make_json_response(exc.message or "Auth Failed", code=exc.code, errmsg=exc.errmsg)

    @app.exception_handler(DecryptedError)
    async def decrypt_exc_handler(request, exc: DecryptedError):
        app_logger.error(f"Decrypt Error! {exc}")
        return make_json_response("decrypt error", code=exc.code, errmsg=default_msg)

    @app.exception_handler(RateLimitExceeded)
    async def limit_exc_handler(request, exc: RateLimitExceeded):
        return make_json_response("Rate limit exceeded", code=429, errmsg="操作太快啦，休息一下吧~")

    @app.exception_handler(PermissionDenied)
    async def permit_denied_exc_handler(request, exc: PermissionDenied):
        return make_json_response(
            exc.message or "permission denied", code=exc.code, errmsg=exc.errmsg
        )
