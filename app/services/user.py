import string
import random
from typing import Literal

from sqlalchemy.ext.asyncio import AsyncSession

from app.ext.jwt import TokenUserInfo
from app.models.user import User
from app.repo.user import UserRepo, user_repo
from app.schemas.user import UpdateUserSchema, UserSchema


class UserService:
    @staticmethod
    def gen_random_username():
        return "用户" + "".join(random.choices(string.ascii_letters + string.digits, k=6))

    @staticmethod
    async def create_user(
        session,
        account: str = None,
        password: str = None,
        username: str = None,
        email: str = None,
        commit=True,
    ):
        if not username:
            username = UserService.gen_random_username()
        user = await user_repo.add(
            session,
            account=account,
            username=username,
            password=password,
            email=email,
            commit=False,
        )
        if commit:
            await session.commit()
        return user

    @staticmethod
    async def check_user_exist(
        session, method: Literal["id", "account", "phone", "email"], value, cond=None
    ) -> User | None:
        if not value:
            return
        if not cond:
            cond = []
        cond.append(getattr(User, method) == value)
        return await user_repo.get_by_cond(session, cond)

    @staticmethod
    async def get_me_detail(session, user: TokenUserInfo) -> UserSchema:
        user_obj = await user_repo.retrieve_or_404(session, user.id)
        userinfo = UserSchema.model_validate(user_obj).model_dump(context={"mask_phone": True})
        return userinfo

    @staticmethod
    async def update_me(session, user, data: UpdateUserSchema):
        user_obj = await user_repo.edit(session, user.id, data.model_dump(exclude_unset=True))
        return user_obj
