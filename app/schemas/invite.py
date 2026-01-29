from datetime import datetime
from typing import Any
from pydantic import BaseModel

from app.constant import InviteState, InviteTargetType
from app.schemas.anniversary import AnnivSchema
from app.schemas.common import EntityModel
from app.schemas.user import ShareGroupShema, SimpleUser


class InviteItem(EntityModel):
    id: str
    ttype: InviteTargetType
    tid: str
    state: InviteState
    invitee_email: str | None = None
    invitee_user_id: int | None = None

    message: str
    expires_at: int
    responded_at: datetime | None = None

    target: AnnivSchema | ShareGroupShema | None = None


class InviteRespondOut(BaseModel):
    status: str
    target_url: str | None = None
