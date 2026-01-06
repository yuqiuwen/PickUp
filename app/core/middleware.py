import json
import itsdangerous

from starlette.concurrency import iterate_in_threadpool
from ulid import ULID
from fastapi import Request
from fastapi.middleware.cors import CORSMiddleware


from app.core.loggers import app_logger


def register_middleware(app):
    # @app.middleware("http")
    # async def auth_middleware(request: Request, call_next):
    #     # 白名单跳过验证
    #     if request.url.path in settings.WHITE_ROUTE_LIST:
    #         return await call_next(request)

    #     for pattern in settings.WHITE_ROUTE_PATTERN:
    #         if pattern.match(request.url.path):
    #             return await call_next(request)

    #     session_id = request.cookies.get("session_id")
    #     if not session_id:
    #         return make_response(
    #             "Session id is missing", errmsg="未登录", code=AppCode.AUTH_INVALID
    #         )

    #     try:
    #         UrlSafeTimedSerializer.loads(session_id, max_age=settings.TOKEN_EXPIRES)
    #     except itsdangerous.SignatureExpired:
    #         return make_response(
    #             "signature is expired", errmsg="登录状态过期", code=AppCode.AUTH_ERROR
    #         )
    #     except itsdangerous.BadSignature:
    #         return make_response("bad signature", errmsg="身份信息无效", code=AppCode.AUTH_ERROR)

    #     user_info = TokenCache(session_id).get()
    #     if not user_info:
    #         return make_response(
    #             "session id is invalid", errmsg="登录状态失效", code=AppCode.AUTH_INVALID
    #         )

    #     user_info = json.loads(user_info)
    #     user_info = UserAuthInfoSchema.model_construct(**user_info)
    #     request.state.current_user = user_info
    #     request.state.session_id = session_id

    #     response = await call_next(request)

    #     return response

    @app.middleware("http")
    async def request_log_middleware(request, call_next):
        request_id = str(ULID())
        log_info = f"{request.method} {request.url.path} {request.state.real_ip} {request_id}"
        if request.query_params:
            log_info += f" | {request.query_params}"
        app_logger.info(log_info)

        response = await call_next(request)
        response.headers["X-Request-Id"] = request_id

        if request.url.path not in {"/docs", "/redoc", "/openapi.json"}:
            response_body = [chunk async for chunk in response.body_iterator]
            response.body_iterator = iterate_in_threadpool(iter(response_body))

            body = json.loads(response_body[0].decode())
            code = body.get("code", response.status_code)
            app_logger.info(f"RESPONSE: {request_id} {code} {request.url.path}")
        return response

    @app.middleware("http")
    async def real_ip_middleware(request: Request, call_next):
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            client_ip = forwarded_for.split(",")[0]  # 取第一个IP
        else:
            client_ip = request.client.host

        # 将IP存入请求状态
        request.state.real_ip = client_ip
        response = await call_next(request)
        return response
