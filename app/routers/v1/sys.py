from fastapi import Request
from slowapi.util import get_remote_address, get_ipaddr

from app.core.http_handler import make_response
from app.ext.limiter import limiter
from app.routers import BaseAPIRouter
from app.schemas.common import EmailSchema
from app.services.email import email_service


router = BaseAPIRouter(prefix="/sys", tags=["sys"])


def get_send_email_code_limit_key(request: Request):
    data = request._json  #
    return f"{get_ipaddr(request)}-{data.get('biz')}-{data.get('email')}"


@router.post("/email/send_code", summary="发送邮箱验证码")
@limiter.limit("2/minute", key_func=get_send_email_code_limit_key)
async def send_email_code(request: Request, data: EmailSchema):
    print(data.email)
    await email_service.send_verify_code(data.email, data.biz)
    return make_response()
