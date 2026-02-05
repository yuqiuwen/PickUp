import string
import random
from typing import List, Literal

from fastapi import HTTPException
from sqlalchemy import Integer, cast, func
from sqlalchemy.ext.asyncio import AsyncSession
from ulid import ULID

from app.constant import GroupRole
from app.ext.jwt import TokenUserInfo
from app.models.user import ShareGroupModel, User
from app.repo.user import UserRepo, share_group_repo, user_repo, user_settings_repo
from app.schemas.user import (
    CreateGroupSchema,
    GroupMemberOptions,
    ShareGroupMemberSchema,
    ShareGroupShema,
    UpdateSettingSchema,
    UpdateUserSchema,
    UserSchema,
)
from app.services.cache.user import UserStatCache
from app.utils.dater import DT


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
    async def get_group_owner_mapping(session, group_id: list[str] | str = None) -> dict[str, int]:
        query = await share_group_repo.list(
            session, group_id, only_cols=[ShareGroupModel.id, ShareGroupModel.owner_id]
        )

        return {i.id: i.owner_id for i in query}

    @staticmethod
    async def get_user_mapping(session, uids: list[int]) -> dict[int, User]:
        data: User = await user_repo.list_by_uid(session, uids, only_cols=UserRepo.BASE_USER_COLS)
        ret = {u.id: u for u in data}
        return ret

    @staticmethod
    async def get_group_list(session, uid: int, search: str):
        items = await share_group_repo.list(session, cur_user_id=uid, kw=search)
        return items

    @staticmethod
    async def get_member_list(session, search: str):
        items = await user_repo.list(session, kw=search, only_cols=UserRepo.BASE_USER_COLS)
        return items

    async def get_group_member_list(self, session, cur_user: TokenUserInfo, search: str):
        groups = await self.get_group_list(session, cur_user.id, search)
        members = await self.get_member_list(session, search)
        return GroupMemberOptions(groups=groups, members=members)

    async def create_group(self, session, user: TokenUserInfo, data: CreateGroupSchema):
        # 暂定为100个限制
        max_members_cnt = 100
        group_id = str(ULID())

        if not data.owner_id:
            data.owner_id = user.id
        if not data.members:
            data.members = {data.owner_id, user.id}
        else:
            data.members = set(data.members) | {data.owner_id, user.id}

        group_data = data.model_dump()
        member_ids = group_data.pop("members")

        group_data.update(
            id=group_id, max_members=max_members_cnt, create_by=user.id, update_by=user.id
        )
        member_data = [
            {
                "user_id": uid,
                "group_id": group_id,
                "role": GroupRole.OWNER if uid == data.owner_id else GroupRole.MEMBER,
            }
            for uid in member_ids
        ]
        ret = await share_group_repo.add(session, group_data, member_data)

        return ret

    @staticmethod
    async def get_group_detail(session, group_id: str) -> ShareGroupShema:
        group = await share_group_repo.retrieve(session, group_id)
        members = group.members
        users = await user_repo.list_by_uid(
            session, {m.user_id for m in members}, only_cols=user_repo.BASE_USER_COLS
        )
        users_mapping = {u.id: u for u in users}

        group_item = ShareGroupShema.model_validate(group)

        members_data = []
        for m in members:
            members_data.append(
                ShareGroupMemberSchema(
                    group_id=m.group_id,
                    user_id=m.user_id,
                    role=m.role,
                    user=users_mapping.get(m.user_id),
                )
            )
        group_item.members = members_data
        return group_item

    @staticmethod
    async def get_stats(session, uid: int):
        ret = await UserStatCache(uid).get(session)

        return ret


class SettingsService:
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
    async def batch_update_setting(session, user: TokenUserInfo, data: List[UpdateSettingSchema]):
        settings = await user_settings_repo.list_setting(
            session, setting_names=[n.name for n in data]
        )
        setting_name_id_map = {s.name: s.id for s in settings}

        ret = await user_settings_repo.edit(
            session,
            user.id,
            [
                {
                    "settings_id": setting_name_id_map[s.name],
                    "user_id": user.id,
                    "value": s.value,
                    "utime": cast(func.extract("epoch", func.now()), Integer),
                }
                for s in data
                if s.name in setting_name_id_map
            ],
        )

        return ret

    @staticmethod
    async def update_setting(session, user: TokenUserInfo, data: UpdateSettingSchema):
        setting = await user_settings_repo.retrieve_setting(session, setting_name=data.name)
        ret = await user_settings_repo.edit(
            session,
            [
                {
                    "settings_id": setting.id,
                    "user_id": user.id,
                    "value": data.value,
                    "utime": cast(func.extract("epoch", func.now()), Integer),
                }
            ],
        )

        return ret
