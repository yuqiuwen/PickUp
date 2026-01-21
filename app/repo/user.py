from operator import imod
from sqlalchemy import Select, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import load_only, noload

from app.models._mixin import BaseMixin
from app.models.sys import SettingsModel
from app.models.user import ShareGroupMemberModel, ShareGroupModel, User, UserSettings
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
        only_cols: list = None,
    ) -> list[ShareGroupModel]:
        if group_id:
            if isinstance(group_id, str):
                where = [self.model.id == group_id]
            else:
                where = [self.model.id.in_(group_id)]

        if owner_id:
            if isinstance(owner_id, int):
                where = [self.model.id == owner_id]
            else:
                where = [self.model.owner_id.in_(owner_id)]

        stmt = select(self.model).where(*where)
        if only_cols:
            stmt = stmt.options(load_only(*only_cols))

        ret = await session.execute(stmt)

        return ret.scalars().all()

    async def list_me_joined_group_ids(self, session: AsyncSession, user_id: int):
        stmt = select(ShareGroupMemberModel.group_id).where(
            ShareGroupMemberModel.user_id == user_id
        )
        ret = await session.execute(stmt)

        return ret.scalars().all()


class UserSettingsRepo(BaseMixin[UserSettings]):
    async def edit(self, session: AsyncSession, user_id: int, data: list[dict], commit=True):
        for item in data:
            item.update(user_id=user_id)
        user = await self.insert_do_update(session, data, commit=commit)
        return user

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


class UserRepo(BaseMixin[User]):
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
        stmt = self.filter(session, *cond)
        if only_cols:
            stmt = stmt.options(load_only(*only_cols))

        ret = await session.execute(stmt)
        return ret.all()

    async def retrieve_or_404(self, session, pk):
        return await self.first_or_404(session, self.model.id == pk)

    async def edit(self, session, pk, data, commit=True):
        user = await self.retrieve_or_404(session, pk)
        user = await self.update(session, user, data, commit=commit)
        return user


user_repo: UserRepo = UserRepo(User)
user_settings_repo: UserSettingsRepo = UserSettingsRepo(UserSettings)
share_group_repo: ShareGroupRepo = ShareGroupRepo(ShareGroupModel)
