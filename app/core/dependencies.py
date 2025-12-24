import importlib
import json
import os
from app.ext.jwt import TokenUserInfo
from app.models.user import User
from fastapi.security import HTTPBearer
from fastapi.security.utils import get_authorization_scheme_param
import itsdangerous
from typing import Annotated

from fastapi import Depends, WebSocketException, status, WebSocket, Cookie
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.requests import Request

from app.config import settings
from app.core.app_code import AppCode
from app.core.exception import AuthException
from app.ext.auth import verify_api_key
from app.database import get_session
from app.schemas.user import UserAuthInfoSchema


def load_config_class():
    config_name = os.getenv("APP_ENV", "development")
    cfg_class_name = f"{config_name.capitalize()}Config"
    config_class = getattr(importlib.import_module("app.config"), cfg_class_name)
    return config_class()



async def get_current_user(request: Request) -> TokenUserInfo:
    return request.user


async def get_current_uid(request: Request) -> int | None:
    return request.user.id


async def get_session_id(request: Request):
    return getattr(request.state, "session_id", None)

    
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



async def get_session_for_ws(
    websocket: WebSocket,
    session: Annotated[str | None, Cookie()] = None,
):
    if session is None:
        raise WebSocketException(code=AppCode.AUTH_INVALID)

    print(session)
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


def require_roles(*required_roles: str):
    # 使用方式：current_user: User = Depends(require_roles("admin", "operator")),

    # 如果函数中无需用到user，可以写到router中：
    # @router.get("/health", dependencies=[Depends(require_roles("admin"))])

    async def dependency(user: User = Depends(get_current_user)) -> User:
        """
        在这里写：当前 user 是否包含 required_roles 之一/全部 的判断，
        如果不满足就 raise HTTPException(403)。
        """
        # 占位：伪代码
        # user_role_names = {role.name for role in user.roles}
        # if not some_check(user_role_names, required_roles):
        #     raise HTTPException(status_code=403, detail="Forbidden")
        return user  # 返回 user，方便在路由里继续用
    return dependency



def require_perms(*required_perms: str):

    # 使用方式
    # @router.get("/orders")
    # async def list_orders(
    #     user: User = Depends(require_perms("order:read")),
    # ):
    #     ...

    
    async def dependency(user: User = Depends(get_current_user)) -> User:
        """
        在这里写：当前 user 是否拥有 required_perms 的判断逻辑。
        """
        # 占位：从 user.roles 里聚合所有 permissions.code 然后判断
        # user_perm_codes = {...}
        # if not some_check(user_perm_codes, required_perms):
        #     raise HTTPException(status_code=403, detail="Forbidden")
        return user
    return dependency


SessionDep = Annotated[AsyncSession, Depends(get_session)]

CurUserDep = Annotated[UserAuthInfoSchema, Depends(get_current_user)]

CurUidDep = Annotated[int, Depends(get_current_uid)]

CurSessionIdDep = Annotated[str, Depends(get_session_id)]

UrlSafeTimedSerializer = itsdangerous.URLSafeTimedSerializer(settings.AUTH_SECRET_KEY)

ApiKeyDep = Annotated[str, Depends(verify_api_key)]

JwtAuthDep = Depends(HTTPBearer())