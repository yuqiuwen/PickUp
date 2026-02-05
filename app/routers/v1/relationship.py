from fastapi import Depends
from app.core.dependencies import RequireAuthDep, SessionDep
from app.core.http_handler import CursorPageRespModel, make_response
from app.routers import BaseAPIRouter
from app.schemas.relationship import FollowItemSchema, QueryFollowSchema
from app.services.relationship import RelationshipService


router = BaseAPIRouter(prefix="/relationship", tags=["relationship"])


@router.get("/follow", response_model=CursorPageRespModel[FollowItemSchema])
async def list_follow(
    session: SessionDep, user: RequireAuthDep, params: QueryFollowSchema = Depends()
):
    ret = await RelationshipService.list_follow(session, user.id, params)
    return make_response(data=ret)


@router.post("/follow")
async def follow(session: SessionDep, user: RequireAuthDep, to_uid: int):
    await RelationshipService.follow(session, user.id, to_uid)
    return make_response()


@router.post("/unfollow")
async def unfollow(session: SessionDep, user: RequireAuthDep, to_uid: int):
    await RelationshipService.unfollow(session, user.id, to_uid)
    return make_response()


@router.get("/fan", response_model=CursorPageRespModel[FollowItemSchema])
async def list_fan(
    session: SessionDep, user: RequireAuthDep, params: QueryFollowSchema = Depends()
):
    ret = await RelationshipService.list_fan(session, user.id, params)
    return make_response(data=ret)
