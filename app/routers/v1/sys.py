from typing import List
from fastapi import Request
from slowapi.util import get_remote_address, get_ipaddr

from app.core.dependencies import RequireAuthDep, SessionDep
from app.core.http_handler import RespModel, make_response
from app.ext.limiter import limiter
from app.routers import BaseAPIRouter
from app.schemas.common import EmailSchema
from app.schemas.user import GroupMemberOptions, ShareGroupShema, SimpleUser
from app.services.email import email_service
from app.services.user import UserService


router = BaseAPIRouter(prefix="/sys", tags=["sys"])


def get_send_email_code_limit_key(request: Request):
    data = request._json  #
    return f"{get_ipaddr(request)}-{data.get('biz')}-{data.get('email')}"


@router.post("/email/send_code", summary="发送邮箱验证码")
@limiter.limit("2/minute", key_func=get_send_email_code_limit_key)
async def send_email_code(request: Request, data: EmailSchema):
    await email_service.send_verify_code(data.email, data.biz)
    return make_response()


@router.get("/groups", summary="获取组列表", response_model=RespModel[List[ShareGroupShema]])
async def get_groups(session: SessionDep, cur_user: RequireAuthDep, search: str):
    data = await UserService.get_group_list(session, search)
    return make_response(data=data)


@router.get("/members", summary="获取用户列表", response_model=RespModel[List[SimpleUser]])
async def get_members(session: SessionDep, cur_user: RequireAuthDep, search: str):
    data = await UserService.get_member_list(session, search)
    return make_response(data=data)


@router.get(
    "/groups_members", summary="获取用户和组列表", response_model=RespModel[GroupMemberOptions]
)
async def get_group_and_members(session: SessionDep, cur_user: RequireAuthDep, search: str):
    data = await UserService().get_group_member_list(session, search)
    return make_response(data=data)
