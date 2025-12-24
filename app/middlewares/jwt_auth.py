from fastapi.requests import HTTPConnection
from fastapi.security.utils import get_authorization_scheme_param
from starlette.authentication import AuthCredentials, AuthenticationBackend, AuthenticationError
from fastapi import Request

from app.config import settings
from app.core.app_code import AppCode
from app.core.exception import AuthException
from app.core.http_handler import make_json_response, make_response
from app.ext.jwt import TokenUserInfo, jwt_manager


class _AuthenticationError(AuthenticationError):
    """重写内部认证错误类"""

    def __init__(
        self,
        *,
        code: int = AppCode.AUTH_ERROR,
        msg: str = "Auth Exception",
        errmsg: str = "认证异常",
    ) -> None:
        """
        初始化认证错误

        :param code: 错误码
        :param msg: 错误信息
        :param headers: 响应头
        :return:
        """
        self.code = code
        self.msg = msg
        self.errmsg = errmsg


class JwtAuthMiddleware(AuthenticationBackend):
    """JWT 认证中间件"""

    @staticmethod
    def auth_exception_handler(conn: HTTPConnection, exc: _AuthenticationError):
        """
        覆盖内部认证错误处理

        :param conn: HTTP 连接对象
        :param exc: 认证错误对象
        :return:
        """
        return make_json_response(exc.msg, code=exc.code, errmsg=exc.errmsg)

    @staticmethod
    async def jwt_authentication(token: str, request) -> TokenUserInfo:
        """
        JWT 认证

        :param token: JWT token
        :return:
        """
        try:
            token_payload = jwt_manager.verify_token(
                token, 
                verify_exp=request.url.path != "/v1/auth/refresh"
            )
            user_id = token_payload.user_id
            userinfo = await jwt_manager.load_from_cache(user_id, token_payload.jti, "access")
            if not userinfo:
                raise _AuthenticationError(code=AppCode.AUTH_INVALID, msg="token expired", errmsg="登录状态已过期")
            return userinfo
        except AuthException as e:
            # 将业务层的 AuthException 转换为 middleware 层的 _AuthenticationError
            raise _AuthenticationError(code=e.code, msg=e.message, errmsg=e.errmsg)

    async def authenticate(self, request: Request) -> tuple[AuthCredentials, TokenUserInfo] | None:
        """
        认证请求

        :param request: FastAPI 请求对象
        :return:
        """

        token = request.headers.get("Authorization")
        path = request.url.path

        if path in settings.WHITE_ROUTE_LIST:
            return
        for pattern in settings.WHITE_ROUTE_PATTERN:
            if pattern.match(path):
                return

        if not token:
            raise _AuthenticationError(code=AppCode.AUTH_INVALID, msg="token is required", errmsg="未登录")

        scheme, token = get_authorization_scheme_param(token)
        if scheme.lower() != "bearer":
            raise _AuthenticationError(msg="invalid token scheme", errmsg="token scheme invalid")

        user = await self.jwt_authentication(token, request)

        return AuthCredentials(["authenticated"]), user
