from types import MappingProxyType
from typing import Annotated, Any, List

from fastapi import Query
from pydantic import BaseModel, Field, field_validator
from app.constant import RemindActionEnum, SysActionEnum, SysAnnounceActionEnum
from app.core.types import TActionEnum
from app.schemas.common import CursorPageQueryModel, EntityModel
from app.schemas.field import DelimitedList
from app.schemas.user import SimpleUser


class QueryRemindNotifySchema(CursorPageQueryModel):
    last: int | None = 0
    actions: str

    @field_validator("actions", mode="after")
    @classmethod
    def parse_actions(cls, v):
        if isinstance(v, str):
            return [int(x) for x in v.split(",")]
        return v


class RemindNotifyItem(EntityModel):
    id: int
    action: int
    ttype: int
    tid: str
    ttime: int
    ctime: int
    user_total: int = 0
    from_users: List[SimpleUser] = Field(default_factory=list)
    to_user: SimpleUser | None = None
    target: Any | None = None


class SysNotifyItem(EntityModel):
    id: int
    action: int
    ttype: int
    tid: str
    ttime: int
    ctime: int
    target: Any | None = None


class AnnounceNotifyItem(EntityModel):
    id: int
    title: int
    content: str
    sent_at: int
    ctime: int


class UnReadMsgCntSchema(BaseModel):
    sys_cnt: int = 0
    announce_cnt: int = 0

    fan_cnt: int = 0
    like_cnt: int = 0
    collect_cnt: int = 0
    comment_cnt: int = 0
    invite_cnt: int = 0
    mention_cnt: int = 0


ACTION_FIELD_NAME_MAPPING = MappingProxyType(
    {
        SysActionEnum.SYS: "sys_cnt",
        SysAnnounceActionEnum.ANNOUNCE: "announce_cnt",
        RemindActionEnum.FAN: "fan_cnt",
        RemindActionEnum.LIKE: "like_cnt",
        RemindActionEnum.COLLECT: "collect_cnt",
        RemindActionEnum.COMMENT: "comment_cnt",
        RemindActionEnum.REPLY: "comment_cnt",
        RemindActionEnum.MENTION: "mention_cnt",
        RemindActionEnum.INVITE: "invite_cnt",
    }
)


EmptyUnReadMsgCnt = UnReadMsgCntSchema().model_dump()
