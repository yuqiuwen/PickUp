from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Literal, Any
import uuid
from fastapi.security.utils import get_authorization_scheme_param
from jose import JWTError, jwt
from jose.exceptions import ExpiredSignatureError
from pydantic import BaseModel, Field
from fastapi import FastAPI, Request

from app.config import settings
from app.core.app_code import AppCode
from app.core.exception import AuthException
from app.services.cache.user import JWTTokenCache


@dataclass
class TokenData:
    user_id: int
    jti: str
    expire: datetime
    flg: Literal["access", "refresh"]


# JWT 配置
class JWTConfig:
    SECRET_KEY: str = settings.TOKEN_SECRET_KEY
    ALGORITHM: str = settings.TOKEN_ALGORITHM
    ACCESS_TOKEN_EXPIRE: int = settings.TOKEN_EXPIRES
    REFRESH_TOKEN_EXPIRE: int = settings.TOKEN_REFRESH_EXPIRE
    COOKIE_REFRESH_TOKEN_KEY: str = settings.COOKIE_REFRESH_TOKEN_KEY
    AC_TOKEN_KEY: str = "access"
    RF_TOKEN_KEY: str = "refresh"


class TokenUserInfo(BaseModel):
    id: int
    username: str
    phone: str | None
    roles: list[str] | None = Field(default_factory=list)


@dataclass
class AccessToken:
    token: str
    expire_in: datetime
    jti: str


@dataclass
class RefreshToken:
    token: str
    expire_in: datetime


@dataclass
class RespLoginSchema:
    access_token: str
    expire_in: int


class JWTManager:
    def __init__(self, app: FastAPI = None):
        self.config = JWTConfig()

    async def create_access_token(
        self,
        sub: str,
        multi_login: bool,
        userinfo: TokenUserInfo,
        additional_claims: dict[str, Any] = None,
    ) -> AccessToken:
        """创建访问令牌"""
        if not isinstance(sub, str):
            sub = str(sub)

        now = datetime.now(timezone.utc)
        expire = now + timedelta(seconds=self.config.ACCESS_TOKEN_EXPIRE)
        jti = str(uuid.uuid4())
        flg = self.config.AC_TOKEN_KEY
        payload = {
            "iat": now,
            "sub": sub,
            "exp": expire,
            "jti": jti,
            "alg": self.config.ALGORITHM,
            "typ": "JWT",
            "flg": flg,
        }
        if additional_claims:
            payload.update(additional_claims)

        encoded_jwt = jwt.encode(payload, self.config.SECRET_KEY, algorithm=self.config.ALGORITHM)

        if not multi_login:
            await JWTTokenCache(flg, sub, "").delete_prefix()

        await JWTTokenCache(flg, sub, jti).add(
            userinfo.model_dump_json(), self.config.ACCESS_TOKEN_EXPIRE
        )

        return AccessToken(token=encoded_jwt, jti=jti, expire_in=expire)

    async def create_refresh_token(
        self,
        sub: str,
        jti: str,
        multi_login: bool,
    ) -> RefreshToken:
        """创建刷新令牌"""

        now = datetime.now(timezone.utc)
        expire = now + timedelta(seconds=self.config.REFRESH_TOKEN_EXPIRE)
        flg = self.config.RF_TOKEN_KEY
        payload = {
            "iat": now,
            "sub": sub,
            "exp": expire,
            "jti": jti,
            "alg": self.config.ALGORITHM,
            "typ": "JWT",
            "flg": flg,
        }

        encoded_jwt = jwt.encode(payload, self.config.SECRET_KEY, algorithm=self.config.ALGORITHM)

        if not multi_login:
            await JWTTokenCache(flg, sub, "").delete_prefix()

        await JWTTokenCache(flg, sub, jti).add(sub, self.config.REFRESH_TOKEN_EXPIRE)

        return RefreshToken(token=encoded_jwt, expire_in=expire)

    def verify_token(self, token: str, verify_exp=True) -> TokenData:
        """验证令牌并返回payload"""
        try:
            payload = jwt.decode(
                token,
                self.config.SECRET_KEY,
                algorithms=[self.config.ALGORITHM],
                options={"verify_exp": verify_exp},
            )
            sub = payload.get("sub")
            jti = payload.get("jti")
            exp = payload.get("exp")
            flg = payload.get("flg")

            if not sub or not jti or not exp:
                raise AuthException("Invalid token", errmsg="token无效")

            return TokenData(
                user_id=int(sub),
                jti=jti,
                expire=datetime.fromtimestamp(exp, tz=timezone.utc),
                flg=flg,
            )

        except ExpiredSignatureError:
            raise AuthException("Token expired", code=AppCode.AUTH_INVALID, errmsg="登录状态已过期")
        except JWTError:
            raise AuthException("Invalid token", errmsg="认证失败")
        except Exception:
            raise AuthException("Invalid token", errmsg="认证失败")

    async def load_from_cache(
        self, user_id: int, jti: str, flg: Literal["access", "refresh"]
    ) -> TokenUserInfo:
        """从缓存中加载令牌, 返回sub"""
        token_cache = await JWTTokenCache(flg, user_id, jti).get()
        if not token_cache:
            raise AuthException("Invalid token", code=AppCode.AUTH_INVALID, errmsg="token无效")
        return TokenUserInfo.model_validate_json(token_cache)

    async def refresh_access_token(
        self, refresh_token: str, multi_login: bool, userinfo: TokenUserInfo
    ) -> tuple[AccessToken, RefreshToken]:
        """使用刷新令牌获取新的访问令牌"""
        token_obj = self.verify_token(refresh_token)
        if not token_obj or token_obj.flg != self.config.RF_TOKEN_KEY:
            raise AuthException("Invalid token", code=AppCode.AUTH_INVALID, errmsg="token无效")

        token_cache = JWTTokenCache(self.config.RF_TOKEN_KEY, token_obj.user_id, token_obj.jti)
        user_id = await token_cache.get()
        if not user_id or int(user_id) != token_obj.user_id:
            raise AuthException("Invalid token", code=AppCode.AUTH_INVALID, errmsg="token无效")

        await token_cache.delete()
        await JWTTokenCache(self.config.AC_TOKEN_KEY, token_obj.user_id, token_obj.jti).delete()

        access_token: AccessToken = await self.create_access_token(user_id, multi_login, userinfo)
        refresh_token: RefreshToken = await self.create_refresh_token(
            user_id, access_token.jti, multi_login
        )

        return access_token, refresh_token

    async def get_token(self, request: Request, verify=False, verify_exp=True) -> TokenData | str:
        """
        获取请求头中的 token

        :param request: FastAPI 请求对象
        :return:
        """
        authorization = request.headers.get("Authorization")
        scheme, token = get_authorization_scheme_param(authorization)
        if not authorization or scheme.lower() != "bearer":
            raise AuthException("Token invalid", errmsg="身份凭证无效")

        if verify:
            token_payload = self.verify_token(token, verify_exp=verify_exp)
            return token_payload
        return token

    async def get_refresh_token(
        self, request: Request, verify=False, verify_exp=True
    ) -> TokenData | str:
        """
        获取refresh token

        :param request: FastAPI 请求对象
        :param verify: 是否验证 token
        :param verify_exp: 是否验证 token 过期时间
        :return:
        """

        token = request.cookies.get(self.config.COOKIE_REFRESH_TOKEN_KEY)
        if verify:
            if not token:
                raise AuthException("Invalid token", code=AppCode.AUTH_INVALID, errmsg="token无效")
            token_payload = self.verify_token(token, verify_exp=verify_exp)
            return token_payload
        return token


jwt_manager = JWTManager()
