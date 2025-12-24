
from app.core.dependencies import CurUserDep, SessionDep
from app.core.http_handler import RespModel, make_response
from app.routers import BaseAPIRouter
from app.schemas.sys import QSecretSchema
from app.services.secret import SecretService



router = BaseAPIRouter(prefix="/secret", tags=["secret"])


@router.post("/rsa_public_key", summary="获取公钥")
async def get_data(cur_user: CurUserDep, params: QSecretSchema):
    data = await SecretService.get_rsa_public_key(params.biz)
    return make_response(data=data)
