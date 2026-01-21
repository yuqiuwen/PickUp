from pydantic import BaseModel

from app.constant import ResourceType, UserInterActionEnum


class DoInteractionSchema(BaseModel):
    rid: str
    rtype: ResourceType
    state: int
