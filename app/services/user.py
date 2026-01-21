import string
import random
from typing import Literal

from sqlalchemy.ext.asyncio import AsyncSession

from app.ext.jwt import TokenUserInfo
from app.models.user import ShareGroupModel, User
from app.repo.user import UserRepo, share_group_repo, user_repo, user_settings_repo
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
        data = {method: value}
        return await user_repo.retrieve(session, **data)

    @staticmethod
    async def get_me_detail(session, user: TokenUserInfo) -> UserSchema:
        user_obj = await user_repo.retrieve_or_404(session, user.id)
        userinfo = UserSchema.model_validate(user_obj).model_dump(context={"mask_phone": True})
        return userinfo

    @staticmethod
    async def update_me(session, user, data: UpdateUserSchema):
        user_obj = await user_repo.edit(session, user.id, data.model_dump(exclude_unset=True))
        return user_obj

    @staticmethod
    async def get_me_settings(
        session, user: TokenUserInfo, setting_name: str = None
    ) -> dict[str, str]:
        """获取我的设置

        Returns:
            dict[str, str]: dict[name, value]
        """
        items = await user_settings_repo.retrieve(session, user.id, setting_name=setting_name)

        ret = {}
        for settings, user_settings in items:
            default_value = settings.value
            user_value = getattr(user_settings, "value", None)
            value = user_value if user_value is not None else default_value
            ret[settings.name] = value

        return ret

    @staticmethod
    async def get_me_one_setting(session, user_id: int, setting_name: str) -> str:
        """获取我的某个设置

        Returns:
            str:
        """
        default_value, user_value = await user_settings_repo.retrieve_one(
            session, user_id, setting_name
        )
        value = user_value if user_value is not None else default_value

        return value

    @staticmethod
    async def get_group_owner_mapping(session, group_id: list[str] | str = None) -> dict[str, int]:
        query = await share_group_repo.list(
            session, group_id, only_cols=[ShareGroupModel.id, ShareGroupModel.owner_id]
        )

        return {i.id: i.owner_id for i in query}

    @staticmethod
    async def get_user_name_mapping(session, uids: list[int]):
        data: User = await user_repo.list_by_uid(session, uids, only_cols=[User.id, User.username])
        ret = {u.id: u.username for u in data}

        return ret
