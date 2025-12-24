from datetime import timedelta, timezone
from typing import Annotated
from fastapi import Depends, Request, Response
from fastapi.security import HTTPBasicCredentials

from app.config import settings
from app.constant import AuthType
from app.core.dependencies import SessionDep, CurSessionIdDep, CurUserDep, CurUidDep
from app.core.http_handler import make_response
from app.routers import BaseAPIRouter
from app.schemas.user import LoginSchema, SignSchema, ModifyPwdSchema, SetPwdSchema, EmailSignSchema, SendEmailCodeSchema
from app.services.auth import AuthService
from app.utils.dater import DT

router = BaseAPIRouter(prefix="/auth", tags=["auth"])


@router.post('/login/swagger', summary='swagger 调试专用', description='用于快捷获取 token 进行 swagger 认证')
async def login_swagger(
    session: SessionDep, obj: Annotated[HTTPBasicCredentials, Depends()]
):
    token, user = await AuthService.swagger_login(session=session, obj=obj)
    return {"access_token": token, "user": user, "token_type": "Bearer"}



@router.post("/login", summary="登录")
async def login(data: LoginSchema, session: SessionDep, response: Response):
    token_type = "jwt"
    auth = AuthService(auth_type=data.auth_type, token_type=token_type)

    if token_type == "sessid":
        await auth.login(session, response, data)   
        return make_response()
    else:
        ret = await auth.login(session, response, data)
        return make_response(data=ret)


@router.post("/signup")
async def signup(data: SignSchema, session: SessionDep):
    auth = AuthService(auth_type=AuthType.ACCOUNT)
    await auth.sign_account(session, data.account, data.pwd)
    return make_response()


@router.post("/signup/email", summary="邮箱注册")
async def signup_by_email(data: EmailSignSchema, session: SessionDep):
    """
    通过邮箱注册账号
    
    - **email**: 邮箱地址
    - **pwd**: 加密后的密码
    - **code**: 邮箱验证码（6位数字）
    """
    auth = AuthService(auth_type=AuthType.EMAIL)
    await auth.sign_email(session, data)
    return make_response(msg="注册成功")


@router.post("/email/send_code", summary="发送邮箱验证码")
async def send_email_code(data: SendEmailCodeSchema):
    """
    发送邮箱验证码
    
    - **email**: 邮箱地址
    - **biz**: 业务场景（sign-注册, login-登录, set_pwd-重置密码）
    """
    from app.services.email import email_service
    from app.constant import SMSSendBiz
    
    # 将字符串转换为枚举
    biz_mapping = {
        "sign": SMSSendBiz.SIGN,
        "login": SMSSendBiz.LOGIN,
        "set_pwd": SMSSendBiz.SET_PWD,
    }
    
    biz_enum = biz_mapping.get(data.biz)
    if not biz_enum:
        from app.core.exception import ValidateError
        raise ValidateError(errmsg="业务场景参数错误")
    
    # 发送验证码
    await email_service.send_verify_code(data.email, biz_enum)
    
    return make_response(msg="验证码已发送，请查收邮件")


@router.post("/logout", summary="退出登录")
async def logout(response: Response, request: Request):
    auth = AuthService(auth_type=AuthType.ACCOUNT)
    ret = await auth.logout_by_jwt(response, request)

    return make_response(data=ret)


@router.post("/pwd_modify", summary="修改密码")
async def modify_password(data: ModifyPwdSchema, session: SessionDep, cur_uid: CurUidDep):
    await AuthService.modify_pwd(session, cur_uid, data)
    return make_response()


@router.post("/pwd_set", summary="初次设置密码")
async def set_password(data: SetPwdSchema, session: SessionDep, cur_uid: CurUidDep):
    user = await AuthService.set_pwd(session, cur_uid, data)
    return make_response(data=user)


@router.post('/refresh', summary='刷新 token')
async def refresh_token(session: SessionDep, response: Response, request: Request):
    data = await AuthService.refresh_token(db=session, response=response, request=request)

    return make_response(data=data)