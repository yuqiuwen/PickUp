from typing import Annotated
from fastapi import Depends, Request, Response
from fastapi.security import HTTPBasicCredentials

from app.constant import AuthType
from app.core.dependencies import RequireAuthDep, SessionDep, CurUidDep
from app.core.http_handler import RespModel, make_response
from app.ext.jwt import RespLoginSchema
from app.routers import BaseAPIRouter
from app.schemas.user import LoginSchema, SignSchema, ModifyPwdSchema, SetPwdSchema, UserSchema
from app.services.auth import AuthService


router = BaseAPIRouter(prefix="/auth", tags=["auth"])


@router.post(
    "/login/swagger", summary="swagger 调试专用", description="用于快捷获取 token 进行 swagger 认证"
)
async def login_swagger(session: SessionDep, obj: Annotated[HTTPBasicCredentials, Depends()]):
    token, user = await AuthService.swagger_login(session=session, obj=obj)
    return {"access_token": token, "user": user, "token_type": "Bearer"}


@router.post("/login", summary="登录", response_model=RespModel[RespLoginSchema])
async def login(data: LoginSchema, session: SessionDep, response: Response):
    token_type = "jwt"
    auth = AuthService(auth_type=data.auth_type, token_type=token_type)
    ret = await auth.login(session, response, data)

    return make_response(data=ret)


@router.post("/signup", response_model=RespModel[RespLoginSchema])
async def signup(data: SignSchema, session: SessionDep, response: Response):
    auth = AuthService(auth_type=data.auth_type)
    ret = await auth.signup(session, response, data)
    return make_response(data=ret)


@router.post("/internal_signup", summary="swagger 内部注册（仅支持账号注册）")
async def internal_signup(data: SignSchema, session: SessionDep):
    auth = AuthService(auth_type=AuthType.ACCOUNT)
    await auth.sign_account(session, data.account, data.pwd)
    return make_response()


@router.post("/logout", summary="退出登录")
async def logout(response: Response, request: Request):
    auth = AuthService(auth_type=AuthType.ACCOUNT)
    ret = await auth.logout_by_jwt(response, request)

    return make_response(data=ret)


@router.post("/reset_password", summary="修改密码", response_model=RespModel[UserSchema])
async def modify_password(data: ModifyPwdSchema, session: SessionDep, cur_uid: CurUidDep):
    await AuthService(data.auth_type).modify_pwd(session, data, cur_uid)
    return make_response()


@router.post("/pwd_set", summary="初次设置密码")
async def set_password(data: SetPwdSchema, session: SessionDep, cur_uid: CurUidDep):
    user = await AuthService.set_pwd(session, cur_uid, data)
    return make_response(data=user)


@router.post("/refresh", summary="刷新 token", response_model=RespModel[RespLoginSchema])
async def refresh_token(
    session: SessionDep, response: Response, request: Request, cur_user: RequireAuthDep
):
    data = await AuthService.refresh_token(
        db=session, response=response, request=request, cur_user=cur_user
    )

    return make_response(data=data)
