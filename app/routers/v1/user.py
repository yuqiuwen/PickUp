
from app.core.dependencies import CurUserDep, SessionDep
from app.core.http_handler import RespModel, make_response
from app.routers import BaseAPIRouter
from app.schemas.user import UserSchema
from app.services.user import UserService


router = BaseAPIRouter(prefix="/me", tags=["me"])


@router.get("", summary="获取我的信息", response_model=RespModel[UserSchema])
async def get_data(session: SessionDep, cur_user: CurUserDep):
    data = await UserService.get_me_detail(session, cur_user)
    return make_response(data=data)
