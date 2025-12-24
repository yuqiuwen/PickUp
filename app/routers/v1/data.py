from app.core.dependencies import ApiKeyDep, CurUserDep, JwtAuthDep, SessionDep
from app.core.http_handler import CursorPageRespModel, PageRespModel, make_response
from app.routers import BaseAPIRouter
from app.schemas.data import PostAssetSchema, QPostAssetSchema
from app.services.data import DataService
from app.utils.paginator import PaginatedResponse


router = BaseAPIRouter(prefix="/data", tags=["data"])


@router.post("/post", summary="获取帖子资源列表", response_model=PageRespModel[PostAssetSchema])
async def get_data(session: SessionDep, data: QPostAssetSchema, cur_user: CurUserDep):
    data = await DataService.get_post_asset(session, data)
    return make_response(data=data)
