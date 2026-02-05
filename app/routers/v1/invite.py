from fastapi import APIRouter, Body, Depends, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Any, Literal

from app.config import settings
from app.constant import InviteState
from app.core.dependencies import RequireAuthDep, SessionDep
from app.core.exception import APIException, PermissionDenied, UserNotFoundError
from app.core.http_handler import RespModel, make_response
from app.routers import BaseAPIRouter
from app.schemas.invite import InviteItem
from app.services.invite import InviteService


router = BaseAPIRouter(prefix="/invite", tags=["invite"])


@router.get("/handle", response_class=HTMLResponse)
async def handle_invite_from_email(
    session: SessionDep, token: str, action: Literal["accept", "decline"]
):
    # deprecated
    try:
        result = await InviteService.handle_invite(
            session=session,
            invite_id=None,
            raw_token=token,
            current_user_id=None,
            action=action,
        )

    except APIException as e:
        return HTMLResponse(f"<h3>{e.errmsg}</h3>", status_code=200)
    except UserNotFoundError:
        register_url = f"{settings.SIGNUP_SITE_URL}?invite_token={token}&action={action}"
        return RedirectResponse(url=register_url, status_code=302)
    except PermissionDenied:
        return HTMLResponse("<h3>该邀请已处理，无需重复操作</h3>", status_code=200)

    if result.state == InviteState.ACCEPTED:
        return HTMLResponse("<h3>你已成功接受邀请</h3>")
    else:
        return HTMLResponse("<h3>你已拒绝该邀请</h3>")


@router.post("/accept", response_model=RespModel[Any])
async def accept_invite(session: SessionDep, user: RequireAuthDep, token: str = Body(embed=True)):
    await InviteService.handle_invite(
        session=session,
        raw_token=token,
        cur_user=user,
        action="accept",
    )
    return make_response()


@router.post("/decline")
async def decline_invite(session: SessionDep, user: RequireAuthDep, token: str):
    await InviteService.handle_invite(
        session=session,
        raw_token=token,
        cur_user=user,
        action="decline",
    )
    return make_response()


@router.get("/preview", response_model=RespModel[InviteItem])
async def preview_invite(session: SessionDep, token: str):
    item = await InviteService.preview_invite(session, token)

    return make_response(data=item)
