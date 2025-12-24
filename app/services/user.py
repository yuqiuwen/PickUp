import string
import random
from typing import Literal

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.repo.user import UserRepo, user_repo
from app.schemas.user import UserAuthInfoSchema, UserSchema


class UserService:
    @staticmethod
    def gen_random_username():
        return "用户" + "".join(random.choices(string.ascii_letters + string.digits, k=6))

    @staticmethod
    async def create_by_account(session, account: str, password: str, commit=True):
        user = await user_repo.create_user(
            session,
            username=UserService.gen_random_username(),
            account=account,
            password=password,
            commit=False,
        )
        if commit:
            await session.commit()
        return user

    @staticmethod
    async def create_by_email(session, email: str, password: str, commit=True):
        """
        通过邮箱创建用户
        
        :param session: 数据库会话
        :param email: 邮箱地址
        :param password: 密码
        :param commit: 是否立即提交
        :return: 用户对象
        """
        user = await user_repo.create_user(
            session,
            username=UserService.gen_random_username(),
            email=email,
            password=password,
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
    async def get_me_detail(session, user: "UserAuthInfoSchema") -> UserSchema:
        user_obj = await user_repo.get_or_404(session, user.id)
        userinfo = UserSchema.model_validate(user_obj).model_dump(context={"mask_phone": True})
        return userinfo
        
