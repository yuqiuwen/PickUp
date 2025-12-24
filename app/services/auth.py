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
from app.constant import AuthType, SMSSendBiz
from app.core.app_code import AppCode
from app.core.dependencies import UrlSafeTimedSerializer
from app.core.exception import AuthException
from app.models.user import User
from app.repo.user import user_repo
from app.schemas.user import (
    LoginSchema,
    UserSchema,
    UserAuthInfoSchema,
    ModifyPwdSchema,
    SetPwdSchema,
    EmailSignSchema,
)
from app.services.cache.sys import VerifyCodeCache
from app.services.cache.user import JWTTokenCache, TokenCache
from app.services.user import UserService
from app.utils.crypto import AesGcmCrypto
from app.utils.dater import DT
from app.ext.jwt import AccessToken, RefreshToken, TokenUserInfo, jwt_manager


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
        userinfo = TokenUserInfo(id=user.id, username=user.username, phone=user.phone, role=None)
        access_token = await jwt_manager.create_access_token(
            user.id,
            multi_login=True,
            userinfo=userinfo,
            # extra info
            additional_claims={"swagger": True},
        )
        return access_token.token, user

    async def sign_account(self, session, account: str, code: str):
        """
        sign account if user not exists
        :return:
        """

        user = None
        try:
            if self.auth_type == AuthType.ACCOUNT:
                if await UserService.check_user_exist(session, "account", account):
                    raise AuthException(code=AppCode.ACCOUNT_EXIST, errmsg="账号已被使用")
                user = await UserService.create_by_account(session, account, code, commit=False)

            await session.commit()
        except IntegrityError:
            raise AuthException(
                "account has been used", code=AppCode.ACCOUNT_EXIST, errmsg="手机号或账号已被绑定"
            )
        if not user:
            raise AuthException(errmsg="注册失败")

        return

    async def sign_email(self, session, data: EmailSignSchema):
        """
        邮箱注册
        
        :param session: 数据库会话
        :param data: 邮箱注册数据
        :return:
        """
        from app.services.email import email_service
        
        user = None
        try:
            # 检查邮箱是否已被使用
            if await UserService.check_user_exist(session, "email", data.email):
                raise AuthException(code=AppCode.ACCOUNT_EXIST, errmsg="邮箱已被使用")
            
            # 验证邮箱验证码
            await email_service.verify_code(data.email, data.code, SMSSendBiz.SIGN)
            
            # 创建用户
            user = await UserService.create_by_email(session, data.email, data.pwd, commit=False)
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
        access_token  = await jwt_manager.create_access_token(
            str(userinfo.id),
            multi_login=is_multi_login,
            userinfo=userinfo
        )
        refresh_token = await jwt_manager.create_refresh_token(
            str(userinfo.id),
            access_token.jti,
            multi_login=is_multi_login,
        )

        return access_token, refresh_token
    
    @staticmethod
    async def refresh_token(db, response, request: Request):
        """
        刷新令牌

        :param db: 数据库会话
        :param request: FastAPI 请求对象
        :return:
        """
        token_payload = await jwt_manager.get_refresh_token(request, verify=True)
        user = await UserService.check_user_exist(db, "id", token_payload.user_id)
        if not user:
            raise AuthException(code=AppCode.ACCOUNT_NOT_EXIST, errmsg="用户不存在")
        
        userinfo = TokenUserInfo(id=user.id, username=user.username, phone=user.phone, role=None)
        access_token, refresh_token = await jwt_manager.refresh_access_token(
            refresh_token,
            True,
            userinfo
        )
        data = {
            "access_token": access_token.token,
            "expire_in": DT.time2ts(access_token.expire_in)
        }
        response.set_cookie(
            key=settings.COOKIE_REFRESH_TOKEN_KEY,
            value=refresh_token.token,
            max_age=settings.TOKEN_REFRESH_EXPIRE,
            expires=refresh_token.expire_in,
            httponly=True,
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

    async def login(self, session, response, data: LoginSchema) -> Tuple[str, UserAuthInfoSchema]:
        """
        login by phone or account
        :return:
        """
        account = data.account
        code = data.code

        # 账密登录
        user = await self.login_by_account(session, account, code)
        user_id = user.id

        # TODO session auth
        if self.token_type == "sessid":
            userinfo = UserAuthInfoSchema(id=user_id, auth_type=self.auth_type)
            session_id = await self.gen_session_id(userinfo)
            await session.commit()

            response.set_cookie(key="session_id", value=session_id, max_age=settings.TOKEN_EXPIRES)
            response.set_cookie(key="user_id", value=user_id, max_age=settings.TOKEN_EXPIRES)
            
        # TODO jwt auth
        else:
            userinfo = TokenUserInfo(id=user_id, username=user.username, phone=user.phone, role=None)
            access_token, refresh_token = await self.gen_jwt_token(userinfo)
            data = {
                "access_token": access_token.token,
                "expire_in": DT.time2ts(access_token.expire_in)
            }

            response.set_cookie(
                key=settings.COOKIE_REFRESH_TOKEN_KEY,
                value=refresh_token.token,
                max_age=settings.TOKEN_REFRESH_EXPIRE,
                expires=refresh_token.expire_in,
                httponly=True,
                secure=True,
            )
    
            return data

    @classmethod
    async def modify_pwd(cls, session, uid, data: ModifyPwdSchema):
        """
        修改密码：支持验证码验证和原密码验证
        :return:
        """

        user: User = await user_repo.get_or_404(session, uid)
        if data.validate_way == "pwd":
            if not user.password_valid(data.cur_pwd):
                raise AuthException(errmsg="当前密码错误")
        elif data.validate_way == "code":
            code = data.code
            if not code:
                raise AuthException(errmsg="验证码不能为空")
            if not user.phone:
                raise AuthException(errmsg="手机号未绑定")
            await VerifyCodeCache(SMSSendBiz.SET_PWD, user.phone).validate(code)

        user.password = data.new_pwd
        await session.commit()
        return user

    @classmethod
    async def set_pwd(cls, session, uid, data: SetPwdSchema):
        """用于初次设置密码"""
        user: User = await user_repo.get_or_404(session, uid)
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