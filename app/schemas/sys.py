from typing import Literal

from pydantic import BaseModel


class QSecretSchema(BaseModel):
    biz: Literal["user_pwd"]