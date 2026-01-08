from datetime import timedelta
import json
import secrets
from time import timezone
from typing import Literal, Tuple
from fastapi import Request, Response
from fastapi.security import HTTPBasicCredentials
import itsdangerous

from sqlalchemy.exc import IntegrityError

from app.config import settings
from app.constant import AuthType, SMSSendBiz, UserRole
from app.core.app_code import AppCode
from app.ext.auth import UrlSafeTimedSerializer
from app.core.exception import AuthException
from app.models.user import User
from app.repo.user import user_repo
from app.schemas.user import (
    LoginSchema,
    SignSchema,
    UserSchema,
    UserAuthInfoSchema,
    ModifyPwdSchema,
    SetPwdSchema,
)
from app.services.cache.sys import VerifyCodeCache
from app.services.cache.user import JWTTokenCache, TokenCache
from app.services.user import UserService
from app.utils.dater import DT
from app.ext.jwt import AccessToken, RefreshToken, RespLoginSchema, TokenUserInfo, jwt_manager


class AuthService:
    def __init__(self, auth_type: AuthType, token_type: Literal["jwt", "sessid"] = "sessid"):
        self.auth_type = auth_type
        self.token_type = token_type

    @classmethod
    async def swagger_login(cls, *, session, obj: HTTPBasicCredentials) -> tuple[str, User]:
        """
        Swagger 文档登录

        :param db: 数据库会话
        :param obj: 登录凭证
        :return:
        """
        user = await cls.login_by_account(session, obj.username, obj.password)
        userinfo = TokenUserInfo(
            id=user.id, username=user.username, phone=user.phone, roles=[UserRole.ADMIN.value]
        )
        access_token = await jwt_manager.create_access_token(
            user.id,
            multi_login=True,
            userinfo=userinfo,
            # extra info
            additional_claims={"swagger": True},
        )
        return access_token.token, user

    async def signup(self, session, response, data: SignSchema):
        if self.auth_type == AuthType.ACCOUNT:
            await self.sign_account(session, data.account, data.pwd)
        elif self.auth_type == AuthType.EMAIL:
            await self.sign_email(session, data.account, data.pwd, data.code, data.username)
        else:
            raise AuthException(errmsg="不支持的注册方式")

        login_schema = LoginSchema.model_validate(
            {
                "auth_type": self.auth_type,
                "account": data.account,
                "code": data.pwd,
                "code_type": "pwd",
            },
            context={"is_encrypted": False},
        )
        ret = await self.login(session, response, login_schema)
        return ret

    async def sign_account(self, session, account: str, code: str, username: str = None):
        """
        sign account if user not exists
        :return:
        """

        user = None
        try:
            if await UserService.check_user_exist(session, "account", account):
                raise AuthException(code=AppCode.ACCOUNT_EXIST, errmsg="账号已被使用")
            user = await UserService.create_user(
                session, account=account, password=code, username=username, commit=False
            )
            await session.commit()
        except IntegrityError:
            raise AuthException(
                "account has been used", code=AppCode.ACCOUNT_EXIST, errmsg="手机号或账号已被绑定"
            )
        if not user:
            raise AuthException(errmsg="注册失败")

        return

    async def sign_email(self, session, email: str, pwd: str, code: str, username: str = None):
        """
        邮箱注册

        :param session: 数据库会话
        :param email: 邮箱地址
        :param pwd: 密码
        :param code: 验证码
        :param username: 用户名
        :return:
        """
        from app.services.email import email_service

        user = None
        try:
            # 检查邮箱是否已被使用
            if await UserService.check_user_exist(session, "email", email):
                raise AuthException(code=AppCode.ACCOUNT_EXIST, errmsg="邮箱已被使用")

            # 验证邮箱验证码
            await email_service.verify_code(email, code, SMSSendBiz.SIGN)

            # 创建用户
            user = await UserService.create_user(
                session, username=username, email=email, password=pwd, commit=False
            )
            await session.commit()

        except IntegrityError:
            raise AuthException(
                "email has been used", code=AppCode.ACCOUNT_EXIST, errmsg="邮箱已被绑定"
            )

        if not user:
            raise AuthException(errmsg="注册失败")

        return user

    @staticmethod
    async def gen_session_id(userinfo: UserAuthInfoSchema):
        userinfo = userinfo.model_dump()
        session_id = UrlSafeTimedSerializer.dumps(userinfo)
        await TokenCache(session_id).add(json.dumps(userinfo), settings.TOKEN_EXPIRES)
        return session_id

    @staticmethod
    async def gen_jwt_token(userinfo: TokenUserInfo) -> tuple[AccessToken, RefreshToken]:
        is_multi_login = True
        access_token = await jwt_manager.create_access_token(
            str(userinfo.id), multi_login=is_multi_login, userinfo=userinfo
        )
        refresh_token = await jwt_manager.create_refresh_token(
            str(userinfo.id),
            access_token.jti,
            multi_login=is_multi_login,
        )

        return access_token, refresh_token

    @staticmethod
    async def refresh_token(
        db, response, request: Request, cur_user: TokenUserInfo
    ) -> RespLoginSchema:
        """
        刷新令牌

        :param db: 数据库会话
        :param request: FastAPI 请求对象
        :return:
        """

        refresh_token = await jwt_manager.get_refresh_token(request, verify=False)
        user = await UserService.check_user_exist(db, "id", cur_user.id)
        if not user:
            raise AuthException(code=AppCode.ACCOUNT_NOT_EXIST, errmsg="用户不存在")

        userinfo = TokenUserInfo(id=user.id, username=user.username, phone=user.phone, roles=[])
        new_access_token, new_refresh_token = await jwt_manager.refresh_access_token(
            refresh_token, True, userinfo
        )
        data = {
            "access_token": new_access_token.token,
            "expire_in": DT.time2ts(new_access_token.expire_in),
        }
        response.set_cookie(
            key=settings.COOKIE_REFRESH_TOKEN_KEY,
            value=new_refresh_token.token,
            max_age=settings.TOKEN_REFRESH_EXPIRE,
            expires=new_refresh_token.expire_in,
            httponly=True,
            secure=True,
        )
        return data

    @classmethod
    async def login_by_account(cls, session, account: str, code: str):
        if not account:
            raise AuthException(errmsg="账号格式错误")

        user = await UserService.check_user_exist(session, "account", account)
        if not user:
            raise AuthException(code=AppCode.ACCOUNT_NOT_EXIST, errmsg="您的账号不存在")
        if not user.password_valid(code):
            raise AuthException("password error", errmsg="密码错误")
        return user

    @classmethod
    async def login_by_email(cls, session, email: str, pwd: str):
        user = await UserService.check_user_exist(session, "email", email)
        if not user:
            raise AuthException(code=AppCode.ACCOUNT_NOT_EXIST, errmsg="您的账号不存在")
        if not user.password_valid(pwd):
            raise AuthException("password error", errmsg="密码错误")
        return user

    async def login(self, session, response, data: LoginSchema) -> RespLoginSchema:
        """
        login by phone or account
        :return:
        """
        account = data.account
        code = data.code

        # 账密登录
        if self.auth_type == AuthType.ACCOUNT:
            user = await self.login_by_account(session, account, code)
        elif self.auth_type == AuthType.EMAIL:
            user = await self.login_by_email(session, account, code)
        else:
            raise AuthException(errmsg="不支持的登录方式")

        user_id = user.id

        userinfo = TokenUserInfo(id=user_id, username=user.username, phone=user.phone, roles=[])
        access_token, refresh_token = await self.gen_jwt_token(userinfo)
        data = {"access_token": access_token.token, "expire_in": DT.time2ts(access_token.expire_in)}

        response.set_cookie(
            key=settings.COOKIE_REFRESH_TOKEN_KEY,
            value=refresh_token.token,
            max_age=settings.TOKEN_REFRESH_EXPIRE,
            expires=refresh_token.expire_in,
            httponly=True,
            secure=True,
        )

        return data

    async def modify_pwd(self, session, data: ModifyPwdSchema, uid=None):
        """
        修改密码：支持验证码验证和原密码验证
        :return:
        """

        if uid:
            user: User = await user_repo.retrieve_or_404(session, uid)
        else:
            if self.auth_type == AuthType.ACCOUNT:
                user = await UserService.check_user_exist(session, "account", data.account)
            elif self.auth_type == AuthType.EMAIL:
                user = await UserService.check_user_exist(session, "email", data.account)
            elif self.auth_type == AuthType.PHONE:
                user = await UserService.check_user_exist(session, "phone", data.account)

        if not user:
            raise AuthException(errmsg="账号不存在")

        if data.validate_way == "pwd":
            if not user.password_valid(data.cur_pwd):
                raise AuthException(errmsg="当前密码错误")

        elif data.validate_way == "code":
            code = data.code
            if not code:
                raise AuthException(errmsg="验证码不能为空")

            match self.auth_type:
                case AuthType.PHONE:
                    verify_account = user.phone
                case AuthType.EMAIL:
                    verify_account = user.email
                case AuthType.ACCOUNT:
                    verify_account = user.account
                case _:
                    raise AuthException(errmsg="不支持的验证方式")

            if not verify_account:
                raise AuthException(errmsg="验证账号不存在")
            await VerifyCodeCache(SMSSendBiz.SET_PWD, verify_account).validate(code)

        user.password = data.new_pwd
        await session.commit()
        return user

    @classmethod
    async def set_pwd(cls, session, uid, data: SetPwdSchema):
        """用于初次设置密码"""
        user: User = await user_repo.retrieve_or_404(session, uid)
        await VerifyCodeCache(SMSSendBiz.SET_PWD, user.phone).validate(data.code)
        user.password = data.new_pwd
        await session.commit()

    @classmethod
    async def canceled(cls, session, uid, phone, code) -> int:
        pass

    @classmethod
    def send_sms(cls, biz: SMSSendBiz, phone: str):
        """
        send sms
        :param biz:
        :param phone:
        :return:
        """

        pass

    @classmethod
    async def logout_by_session(cls, session_id: str, response: Response):
        ret = await TokenCache(session_id).delete()
        response.delete_cookie("session_id")
        response.delete_cookie("user_id")

        return ret

    @classmethod
    async def logout_by_jwt(cls, response: Response, request: Request):
        ac_token_paylod = await jwt_manager.get_token(request, verify=True)
        rf_token = await jwt_manager.get_refresh_token(request, verify=False)
        user_id = ac_token_paylod.user_id
        jti = ac_token_paylod.jti

        response.delete_cookie(settings.COOKIE_REFRESH_TOKEN_KEY)
        await JWTTokenCache("access", user_id, jti).delete()

        if rf_token:
            await JWTTokenCache("refresh", user_id, jti).delete()

        return
