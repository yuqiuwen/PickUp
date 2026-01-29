from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Annotated, List, Literal


from app.core.dependencies import RequireAuthDep, SessionDep
from app.core.exception import APIException, PermissionDenied, UserNotFoundError
from app.core.http_handler import CursorPageRespModel, RespModel, make_response
from app.routers import BaseAPIRouter
from app.schemas.anniversary import AnnivFeedItem, AnnivStat, CreateAnnivSchema, QueryAnnivSchema
from app.services.anniversary import AnnivService
from app.services.invite import InviteService


router = BaseAPIRouter(prefix="/anniv", tags=["anniversary"])


@router.post("")
async def create_anniv(session: SessionDep, cur_user: RequireAuthDep, data: CreateAnnivSchema):
    await AnnivService(data.type).create_anniv(session, cur_user, data)

    return make_response()


@router.get("/stat", response_model=RespModel[AnnivStat])
async def get_anniv_stat(session: SessionDep, cur_user: RequireAuthDep):
    ret = await AnnivService.get_base_stat(
        session,
        cur_user,
    )

    return make_response(data=ret)


@router.get("/feed", response_model=CursorPageRespModel[AnnivFeedItem])
async def get_my_anniv_list(
    session: SessionDep, cur_user: RequireAuthDep, params: QueryAnnivSchema = Depends()
):
    ret = await AnnivService.get_anniv_feed(session, cur_user, params)

    return make_response(data=ret)


@router.get("/{pk}", response_model=RespModel[AnnivFeedItem])
async def get_anniv(session: SessionDep, cur_user: RequireAuthDep, pk: str):
    ret = await AnnivService.get_anniv(session, cur_user, pk)

    return make_response(data=ret)
