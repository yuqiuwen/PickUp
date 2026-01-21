from app.core.dependencies import RequireAuthDep, SessionDep
from app.core.http_handler import RespModel, make_response
from app.routers import BaseAPIRouter
from app.schemas.action import DoInteractionSchema
from app.schemas.sys import QSecretSchema
from app.services.secret import SecretService


router = BaseAPIRouter(prefix="/interaction", tags=["interaction"])


@router.post("/like", summary="点赞", response_model=RespModel[int])
async def do_like(session: SessionDep, cur_user: RequireAuthDep, data: DoInteractionSchema):
    data = 1
    return make_response(data=data)


@router.post("/collect", summary="收藏", response_model=RespModel[int])
async def do_collect(session: SessionDep, cur_user: RequireAuthDep, data: DoInteractionSchema):
    data = 1
    return make_response(data=data)
