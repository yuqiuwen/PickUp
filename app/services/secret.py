import os
from typing import Literal
from app.config import settings


class SecretService:
    @staticmethod
    async def get_rsa_public_key(biz: Literal["user_pwd"]):
        if biz == "user_pwd":
            ret = os.getenv("PWD_PUBLIC_KEY")
            return {"public_key": ret}
       