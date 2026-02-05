import asyncio
from typing import List
from app.core.dependencies import RequireAuthDep, SessionDep
from app.core.http_handler import RespModel, make_response
from app.models.user import UserSettings
from app.routers import BaseAPIRouter
from app.schemas.user import UpdateSettingSchema, UpdateUserSchema, UserSchema, UserStats
from app.services.user import SettingsService, UserService


router = BaseAPIRouter(prefix="/me", tags=["me"])


@router.get("", summary="获取我的信息", response_model=RespModel[UserSchema])
async def get_data(session: SessionDep, cur_user: RequireAuthDep):
    data = await UserService.get_me_detail(session, cur_user)
    return make_response(data=data)


@router.put("", summary="更新我的信息", response_model=RespModel[UserSchema])
async def update_data(session: SessionDep, cur_user: RequireAuthDep, data: UpdateUserSchema):
    data = await UserService.update_me(session, cur_user, data)
    return make_response(data=data)


@router.get("/settings", summary="获取我的设置", response_model=RespModel[dict[str, str]])
async def get_settings(session: SessionDep, cur_user: RequireAuthDep):
    data = await SettingsService.get_me_settings(session, cur_user)
    return make_response(data=data)


@router.post("/settings", summary="更新设置")
async def update_settings(
    session: SessionDep, cur_user: RequireAuthDep, data: List[UpdateSettingSchema]
):
    if len(data) == 1:
        ret = await SettingsService.update_setting(session, cur_user, data[0])
    else:
        ret = await SettingsService.batch_update_setting(session, cur_user, data)
    return make_response(data=ret)


@router.get("/stats", summary="获取我的统计", response_model=RespModel[UserStats])
async def get_stats(session: SessionDep, cur_user: RequireAuthDep):
    data = await UserService.get_stats(session, cur_user.id)
    return make_response(data=data)
