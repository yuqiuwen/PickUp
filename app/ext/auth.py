import json
from typing import Annotated
from fastapi import Depends, Request
from fastapi.security import APIKeyHeader
from fastapi import WebSocketException, status, WebSocket, Cookie
from fastapi.security.utils import get_authorization_scheme_param
import itsdangerous
from starlette.authentication import UnauthenticatedUser

from app.config import settings
from app.core.app_code import AppCode
from app.core.exception import AuthException
from app.ext.jwt import TokenUserInfo
from app.schemas.user import UserAuthInfoSchema


api_key_header = APIKeyHeader(name="X-API-KEY", auto_error=False)


async def verify_api_key(key: str = Depends(api_key_header)):
    if key not in settings.API_KEYS:
        raise AuthException(code=AppCode.AUTH_INVALID)
    return key


async def get_current_user(request: Request) -> TokenUserInfo | UnauthenticatedUser | None:
    return request.user


async def get_current_uid(request: Request) -> int | None:
    return getattr(await get_current_user(request), "id", None)


async def get_session_id(request: Request):
    return getattr(request.state, "session_id", None)


async def require_auth(request: Request) -> TokenUserInfo:
    user = await get_current_user(request)
    if not user or isinstance(user, UnauthenticatedUser):
        raise AuthException(
            code=AppCode.AUTH_INVALID, message="require authentication", errmsg="未登录"
        )
    return user


async def require_uid(request: Request) -> int:
    user = await require_auth(request)
    return user.id


# async def get_current_user(request: Request) -> UserAuthInfoSchema | None:
#     # session方式
#     return getattr(request.state, "current_user", None)


# async def get_current_uid(request: Request) -> int | None:
#     # session方式
#     cur_user = getattr(request.state, "current_user", None)
#     return cur_user and cur_user.id


def get_jwt_token(request: Request) -> str:
    """
    获取请求头中的 token

    :param request: FastAPI 请求对象
    :return:
    """
    authorization = request.headers.get("Authorization")
    scheme, token = get_authorization_scheme_param(authorization)
    if not authorization or scheme.lower() != "bearer":
        raise AuthException(errmsg="登录凭证无效")
    return token


UrlSafeTimedSerializer = itsdangerous.URLSafeTimedSerializer(settings.AUTH_SECRET_KEY)


async def get_session_for_ws(
    websocket: WebSocket,
    session: Annotated[str | None, Cookie()] = None,
):
    if session is None:
        raise WebSocketException(code=AppCode.AUTH_INVALID)

    from app.services.cache.user import TokenCache

    session_id = session.get("session_id")
    if not session_id:
        raise WebSocketException(code=AppCode.AUTH_INVALID, reason="未登录")

    try:
        UrlSafeTimedSerializer.loads(session_id, max_age=settings.TOKEN_EXPIRES)
    except itsdangerous.SignatureExpired:
        raise WebSocketException(code=status.WS_1008_POLICY_VIOLATION, reason="登录状态过期")
    except itsdangerous.BadSignature:
        raise WebSocketException(code=status.WS_1008_POLICY_VIOLATION, reason="身份信息无效")

    user_info = await TokenCache(session_id).get()
    if not user_info:
        raise WebSocketException(code=AppCode.AUTH_INVALID, reason="登录状态失效")

    user_info = json.loads(user_info)
    user_info = UserAuthInfoSchema.model_construct(**user_info)

    return user_info
