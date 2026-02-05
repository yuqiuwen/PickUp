from operator import imod
from typing import List
from fastapi import HTTPException
from sqlalchemy import Select, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import load_only, noload

from app.models._mixin import BaseMixin
from app.models.sys import SettingsModel
from app.models.user import ShareGroupMemberModel, ShareGroupModel, User, UserSettings
from app.schemas.user import CreateGroupSchema, SimpleUser
from app.utils.paginator import Paginator


class ShareGroupRepo(BaseMixin[ShareGroupModel]):
    async def retrieve(self, session: AsyncSession, group_id: str) -> ShareGroupModel:
        item = await self.get_or_404(session, group_id)
        return item

    async def list_paged(
        self,
        session: AsyncSession,
        page=1,
        limit=50,
        group_id: str = None,
        name: str = None,
        is_public: bool = None,
    ):
        cond = []
        if group_id:
            cond.append(self.model.id == group_id)
        if name:
            cond.append(self.model.name.ilike(f"%{name}%"))
        if is_public:
            cond.append(self.model.is_public == is_public)
        stmt = self.filter(*cond)

        paged = await Paginator(session).paginate(stmt, page, limit)
        return paged

    async def list(
        self,
        session: AsyncSession,
        group_id: list[str] | str = None,
        owner_id: list[int] | int = None,
        name: str = None,
        kw: str = None,
        cur_user_id: int = None,
        only_cols: list = None,
        load_members=True,
    ) -> list[ShareGroupModel]:
        where = []

        if group_id:
            if isinstance(group_id, str):
                where.append(self.model.id == group_id)
            else:
                where.append(self.model.id.in_(group_id))
        if name:
            where.append(self.model.name.ilike(f"%{name}%"))

        if owner_id:
            if isinstance(owner_id, int):
                where.append(self.model.owner_id == owner_id)
            else:
                where.append(self.model.owner_id.in_(owner_id))

        if cur_user_id:
            where.append(
                or_(
                    self.model.is_public == 1,
                    (self.model.is_public == 0) & (self.model.members.any(user_id=cur_user_id)),
                )
            )

        if kw:
            if kw.isdigit():
                where.append(or_(self.model.name.ilike(f"%{kw}%"), self.model.id == kw))
            else:
                where.append(self.model.name.ilike(f"%{kw}%"))

        stmt = select(self.model).where(*where).order_by(self.model.id.desc())
        if only_cols:
            stmt = stmt.options(load_only(*only_cols))
        if not load_members:
            stmt = stmt.options(noload(self.model.members))

        ret = await session.execute(stmt)

        return ret.unique().scalars().all()

    async def add(
        self, session: AsyncSession, group_data: dict, member_data: List[dict], commit=True
    ):
        group = await self.create(session, group_data, commit=False)

        if member_data:
            await session.run_sync(
                lambda s: s.bulk_insert_mappings(ShareGroupMemberModel, member_data)
            )
        commit and await session.commit()
        return group

    async def list_me_joined_group_ids(self, session: AsyncSession, user_id: int):
        stmt = select(ShareGroupMemberModel.group_id).where(
            ShareGroupMemberModel.user_id == user_id
        )
        ret = await session.execute(stmt)

        return ret.scalars().all()

    async def list_members_of_group(self, session: AsyncSession, group_id: str):
        stmt = select(ShareGroupMemberModel).where(group_id=group_id)
        ret = await session.execute(stmt)
        return ret.scalars().all()


class UserSettingsRepo(BaseMixin[UserSettings]):
    async def edit(self, session: AsyncSession, data: List[dict], commit=True):
        if not data:
            raise HTTPException(status_code=404)
        ret = await self.insert_do_update(
            session,
            data,
            index_elements=[self.model.settings_id, self.model.user_id],
            commit=commit,
        )
        return ret

    async def retrieve(
        self, session: AsyncSession, user_id: int, setting_name: str = None
    ) -> list[tuple[SettingsModel, UserSettings]]:
        cond = [SettingsModel.state == 1]

        if setting_name is not None:
            cond.append(SettingsModel.name == setting_name)
        stmt = (
            select(SettingsModel, self.model)
            .outerjoin(
                self.model,
                (SettingsModel.id == self.model.settings_id) & (self.model.user_id == user_id),
            )
            .filter(*cond)
            .options(
                load_only(self.model.value),
                load_only(SettingsModel.name, SettingsModel.value, SettingsModel.group),
            )
        )
        items = (await session.execute(stmt)).all()
        return items

    async def retrieve_one(
        self, session: AsyncSession, user_id: int, setting_name: str
    ) -> tuple[str, str | None]:
        cond = [
            SettingsModel.state == 1,
            SettingsModel.name == setting_name,
        ]

        stmt = (
            select(SettingsModel.value, self.model.value)
            .outerjoin(
                self.model,
                (SettingsModel.id == self.model.settings_id) & (self.model.user_id == user_id),
            )
            .filter(*cond)
        )
        items = (await session.execute(stmt)).one()
        return items

    async def retrieve_setting(self, session, setting_name: str = None, setting_id: int = None):
        cond = [SettingsModel.state == 1]
        if setting_name:
            cond.append(SettingsModel.name == setting_name)
        if setting_id:
            cond.append(SettingsModel.id == setting_id)

        stmt = select(SettingsModel).where(*cond)
        query = await session.execute(stmt)

        return query.scalar_one_or_none()

    async def list_setting(
        self, session, setting_names: List[str] = None, setting_ids: List[int] = None
    ):
        cond = [SettingsModel.state == 1]
        if setting_names:
            cond.append(SettingsModel.name.in_(setting_names))
        if setting_ids:
            cond.append(SettingsModel.id.in_(setting_ids))

        stmt = select(SettingsModel).where(*cond)
        query = await session.execute(stmt)

        return query.scalars().all()


class UserRepo(BaseMixin[User]):
    BASE_USER_COLS = [getattr(User, c) for c in SimpleUser.model_fields.keys()]

    async def add(self, session, commit=True, **data):
        user = await self.create(session, data, commit=commit)
        return user

    async def retrieve(self, session, id=None, account=None, phone=None, email=None):
        cond = []
        if id:
            cond.append(self.model.id == id)
        if account:
            cond.append(self.model.account == account)
        if phone:
            cond.append(self.model.phone == phone)
        if email:
            cond.append(self.model.email == email)
        return await self.filter_one(session, *cond)

    async def list_by_uid(self, session, user_ids: list[int] | int, only_cols: list = None):
        cond = []
        if isinstance(user_ids, int):
            cond.append(self.model.id == user_ids)
        else:
            cond.append(self.model.id.in_(user_ids))
        stmt = self.filter(*cond)
        if only_cols:
            stmt = stmt.options(load_only(*only_cols))

        ret = await session.execute(stmt)
        return ret.scalars().all()

    async def list(self, session, kw: str = None, only_cols=None):
        where = []
        if kw:
            if kw.isdigit():
                where.append(or_(self.model.username.ilike(f"%{kw}%"), self.model.id == int(kw)))
            else:
                where.append(self.model.username.ilike(f"%{kw}%"))

        stmt = select(self.model).where(*where)
        if only_cols:
            stmt = stmt.options(load_only(*only_cols))

        ret = await session.execute(stmt)
        return ret.scalars().all()

    async def retrieve_or_404(self, session, pk):
        return await self.first_or_404(session, self.model.id == pk)

    async def edit(self, session, pk, data, commit=True):
        user = await self.retrieve_or_404(session, pk)
        user = await self.update(session, user, data, commit=commit)
        return user


user_repo: UserRepo = UserRepo(User)
user_settings_repo: UserSettingsRepo = UserSettingsRepo(UserSettings)
share_group_repo: ShareGroupRepo = ShareGroupRepo(ShareGroupModel)
