from typing import TypeVar

from sqlalchemy.orm import DeclarativeBase

from app.constant import RemindActionEnum, SysActionEnum, SysAnnounceActionEnum


Model = TypeVar("Model", bound=DeclarativeBase)


TActionEnum = RemindActionEnum | SysAnnounceActionEnum | SysActionEnum
