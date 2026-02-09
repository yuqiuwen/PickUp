from fastapi import Depends
from app.core.dependencies import RequireAuthDep, SessionDep
from app.core.http_handler import CursorPageRespModel, RespModel, make_response
from app.routers import BaseAPIRouter
from app.schemas.notification import (
    AnnounceNotifyItem,
    QueryRemindNotifySchema,
    RemindNotifyItem,
    SysNotifyItem,
    UnReadMsgCntSchema,
)
from app.services.notification import AnnounceNtfyService, RemindNtfyService, SysNtfyService


router = BaseAPIRouter(prefix="/notification", tags=["notification"])


@router.get("/remind", response_model=CursorPageRespModel[RemindNotifyItem])
async def list_remind_notification(
    session: SessionDep, user: RequireAuthDep, params: QueryRemindNotifySchema = Depends()
):
    ret = await RemindNtfyService().list(session, user, params)
    return make_response(data=ret)


@router.get("/sys", response_model=CursorPageRespModel[SysNotifyItem])
async def list_sys_notification(
    session: SessionDep, user: RequireAuthDep, params: QueryRemindNotifySchema = Depends()
):
    ret = await SysNtfyService().list(session, user, params)
    return make_response(data=ret)


@router.get("/announce", response_model=CursorPageRespModel[AnnounceNotifyItem])
async def list_announce_notification(
    session: SessionDep, user: RequireAuthDep, params: QueryRemindNotifySchema = Depends()
):
    ret = await AnnounceNtfyService().list(session, user, params)
    return make_response(data=ret)


@router.post("/cursor")
async def update_remind_cursor(session: SessionDep, user: RequireAuthDep, data: dict[int, int]):
    ret = await RemindNtfyService.update_cursor(session, user, data)
    return make_response(data=ret)


@router.get("/unread", response_model=RespModel[UnReadMsgCntSchema])
async def get_unread_msg_cnt(session: SessionDep, user: RequireAuthDep):
    ret = await RemindNtfyService().get_unread_msgcounts(session, user.id)
    return make_response(data=ret)


@router.get("/reset_all")
async def reset_all_msg_cnt(session: SessionDep, user: RequireAuthDep):
    ret = await RemindNtfyService().reset_all_msgcounts(session, user.id)
    return make_response(data=ret)
