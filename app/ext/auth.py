from fastapi import Depends
from fastapi.security import APIKeyHeader

from app.config import settings
from app.core.app_code import AppCode
from app.core.exception import AuthException


api_key_header = APIKeyHeader(name="X-API-KEY", auto_error=False)


async def verify_api_key(key: str = Depends(api_key_header)):
    if key not in settings.API_KEYS:
        raise AuthException(code=AppCode.AUTH_INVALID)
    return key
