import importlib
import json
import os

from fastapi import Depends
from app.ext.jwt import TokenUserInfo
from app.models.user import User
from fastapi.security import HTTPBearer
from fastapi.security.utils import get_authorization_scheme_param
import itsdangerous
from typing import Annotated


from sqlalchemy.ext.asyncio import AsyncSession

from app.ext.auth import (
    get_current_uid,
    get_current_user,
    get_session_id,
    require_auth,
    require_uid,
    verify_api_key,
)
from app.database import get_session
from app.schemas.user import UserAuthInfoSchema


SessionDep = Annotated[AsyncSession, Depends(get_session)]

CurUserDep = Annotated[UserAuthInfoSchema, Depends(get_current_user)]

RequireAuthDep = Annotated[TokenUserInfo, Depends(require_auth)]

CurUidDep = Annotated[int, Depends(get_current_uid)]

RequireUidDep = Annotated[int, Depends(require_uid)]

CurSessionIdDep = Annotated[str, Depends(get_session_id)]

ApiKeyDep = Annotated[str, Depends(verify_api_key)]

JwtAuthDep = Depends(HTTPBearer())
