from app.models.base import BaseModel
from app.schemas.common import CursorPageQueryModel, EntityModel
from app.schemas.user import SimpleUser


class QueryFollowSchema(CursorPageQueryModel):
    last: int = 0
    username: str | None = None


class FollowItemSchema(EntityModel):
    id: int
    ctime: int
    utime: int
    state: int
    user: SimpleUser
