from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Literal

from app.config import settings
from app.constant import InviteState
from app.core.dependencies import SessionDep
from app.core.exception import APIException, PermissionDenied, UserNotFoundError
from app.routers import BaseAPIRouter
from app.services.invite import InviteService


router = BaseAPIRouter(prefix="/invite", tags=["invite"])


@router.get("/handle", response_class=HTMLResponse)
async def handle_invite_from_email(
    session: SessionDep, token: str, action: Literal["accept", "decline"]
):
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

    # 方式1：直接返回一个简单 HTML 提示
    if result.state == InviteState.ACCEPTED:
        return HTMLResponse("<h3>你已成功接受邀请</h3>")
    else:
        return HTMLResponse("<h3>你已拒绝该邀请</h3>")

    # 方式2：也可以重定向到前端某个页面（如 App H5）
    # return RedirectResponse(f"https://your-frontend.com/anniversaries/invites/result?status={result.status}")
