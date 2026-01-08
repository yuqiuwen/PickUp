import asyncio
from app.core.dependencies import CurUserDep, RequireAuthDep, SessionDep
from app.core.exception import APIException
from app.core.http_handler import RespModel, make_response
from app.routers import BaseAPIRouter
from app.schemas.user import UpdateUserSchema, UserSchema
from app.services.user import UserService


router = BaseAPIRouter(prefix="/me", tags=["me"])


@router.get("", summary="获取我的信息", response_model=RespModel[UserSchema])
async def get_data(session: SessionDep, cur_user: RequireAuthDep):
    data = await UserService.get_me_detail(session, cur_user)
    return make_response(data=data)


@router.put("", summary="更新我的信息", response_model=RespModel[UserSchema])
async def update_data(session: SessionDep, cur_user: RequireAuthDep, data: UpdateUserSchema):
    data = await UserService.update_me(session, cur_user, data)
    return make_response(data=data)
