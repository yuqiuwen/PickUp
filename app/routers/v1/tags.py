from app.core.dependencies import RequireAuthDep, SessionDep
from app.core.exception import APIException, PermissionDenied, UserNotFoundError
from app.core.http_handler import RespModel, make_response
from app.routers import BaseAPIRouter
from app.schemas.common import TagsSchema
from app.services.tags import TagService


router = BaseAPIRouter(prefix="/tags", tags=["tag"])


@router.get("", response_model=RespModel[list[TagsSchema]])
async def get_tag_list(session: SessionDep, search: str):
    ret = await TagService.list_tag(session, search)

    return make_response(data=ret)


@router.post("")
async def create_tags(session: SessionDep, cur_user: RequireAuthDep, names: list[str]):
    ret = await TagService.add_tag(session, cur_user, names)

    return make_response(data=ret)
