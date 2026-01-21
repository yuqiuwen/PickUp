from typing import List
from redis import retry
from sqlalchemy import BigInteger, and_, cast, delete, exists, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql import func, case
from ulid import ULID

from app.constant import AnniversaryType, RepeatType
from app.models._mixin import BaseMixin
from app.models.anniversary import (
    AnnivMediaModel,
    AnniversaryModel,
    AnniversaryMemberModel,
    AnniversaryTag,
    ReminderRule,
    ReminderSlot,
)
from app.models.base import StateModel
from app.models.tags import TagModel
from app.repo.media import media_repo
from app.repo.user import share_group_repo
from app.schemas.anniversary import CreateTagSchema, QueryAnnivSchema, RemindRuleSchema
from app.schemas.common import UpdateMediaSchema
from app.utils.common import diff_sequence_data, parse_sort_str
from app.utils.dater import DT
from app.utils.paginator import CursorPaginatedResponse, ScrollPaginator


class AnnivMemberRepo(BaseMixin[AnniversaryMemberModel]):
    async def batch_add(self, session, data: list[dict], commit=True):
        ret = await self.insert_do_update(
            session, data, constraint="uq_anniversary_member_anniv_idttypetid", commit=commit
        )
        return ret


class TagRepo(BaseMixin[TagModel]):
    async def edit(
        self, session, create_by: int, data: List[CreateTagSchema], commit=True
    ) -> list[dict]:
        if not data:
            return []
        data = [{"name": item.name, "create_by": create_by} for item in data]
        items = await self.insert_or_ignore(
            session,
            data,
            index_elements=["name"],
            returning=(self.model.id, self.model.name),
            commit=commit,
        )
        return [{"id": item.id, "name": item.name} for item in items]


class AnnivRepo(BaseMixin[AnniversaryModel]):
    async def add(self, session, data: dict, commit=True):
        item = await self.create(session, data, commit=commit)
        return item

    async def get_share_stmt(self, session, cur_user_id):
        exist_cond = []
        share_group_ids = await share_group_repo.list_me_joined_group_ids(session, cur_user_id)
        where_stmt_member = and_(
            AnniversaryMemberModel.ttype == 2, AnniversaryMemberModel.tid == str(cur_user_id)
        )
        exist_cond.append(where_stmt_member)
        if share_group_ids:
            where_stmt_group = and_(
                AnniversaryMemberModel.ttype == 1, AnniversaryMemberModel.tid.in_(share_group_ids)
            )
            exist_cond.append(
                or_(
                    where_stmt_member,
                    where_stmt_group,
                )
            )

        member_or_group_exists = exists(select(1).where(*exist_cond))
        return member_or_group_exists

    async def list_feed(self, session: AsyncSession, cur_user_id: int, params: QueryAnnivSchema):
        """list feeds, include:
        owner + share member + share group

        Args:
            session (_type_): _description_
            cur_user_id (int): _description_
            params (QueryAnnivSchema): _description_
        """
        now = DT.now_time()

        cond = [self.model.state == 1]
        if params.event_year:
            cond.append(self.model.event_year == params.event_year)

        if params.type is not None and params.type != "all":
            cond.append(self.model.type == int(params.type))

        if params.order_by == "default":
            orders = (
                case((self.model.next_trigger_at < now, 1), else_=0).label("is_past").asc(),
                case(
                    (self.model.next_trigger_at >= now, self.model.next_trigger_at), else_=None
                ).asc(),
                case(
                    (self.model.next_trigger_at < now, self.model.next_trigger_at), else_=None
                ).desc(),
            )
        else:
            orders = (
                getattr(getattr(self.model, col), sort)() for col, sort in params.order_by.items()
            )

        member_or_group_exists = await self.get_share_stmt(session, cur_user_id)

        stmt = (
            select(self.model)
            .where(
                *cond,
                or_(
                    self.model.owner_id == cur_user_id,
                    and_(self.model.share_mode == 1, member_or_group_exists),
                ),
            )
            .order_by(*orders, self.model.id.desc())
            .limit(1000)
        )

        query = (await session.execute(stmt)).scalars().all()

        return CursorPaginatedResponse(last=0, has_more=False, items=query)

    async def get_year_total(self, session, cur_user_id: int, year: int):
        stmt = select(func.count(self.model.id)).where(
            self.model.state == 1,
            self.model.owner_id == cur_user_id,
            or_(
                and_(
                    self.model.next_trigger_at >= DT.str2date(f"{year}-01-01"),
                    self.model.next_trigger_at <= DT.str2date(f"{year}-12-31"),
                ),
                self.model.type == AnniversaryType.BIRTHDAY,  # birth every year
            ),
        )
        total = (await session.execute(stmt)).scalar() or 0
        return total

    async def get_next(self, session, cur_user_id: int):
        member_or_group_exists = await self.get_share_stmt(session, cur_user_id)
        stmt = (
            select(self.model)
            .where(
                self.model.state == 1,
                self.model.next_trigger_at >= DT.now_ts(),
                self.model.repeat_type == RepeatType.NONE,
                or_(
                    self.model.owner_id == cur_user_id,
                    and_(self.model.share_mode == 1, member_or_group_exists),
                ),
            )
            .order_by(self.model.next_trigger_at)
            .limit(1)
        )

        result = await session.execute(stmt)
        return result.scalar_or_none()

    async def retrieve_or_404(self, session, anniv_id: str):
        item = await self.first_or_404(self.model.state == 1, self.model.id == anniv_id)
        return item

    async def add_tag(
        self, session, anniv_id: str, create_by: int, tags: List[CreateTagSchema], commit=True
    ):
        new_tags = await tag_repo.edit(
            session, create_by, [i for i in tags if not i.id], commit=False
        )
        tag_ids = {i.id for i in tags if i.id} | {i["id"] for i in new_tags}

        to_add_data = [{"anniv_id": anniv_id, "tag_id": tid} for tid in tag_ids]
        await session.run_sync(lambda s: s.bulk_insert_mappings(AnniversaryTag, to_add_data))

        commit and await session.commit()

    async def update_tag(
        self, session, anniv_id: str, create_by: int, tags: List[CreateTagSchema], commit=True
    ):
        old_anniv_tag_ids = (
            await (
                session.execute(
                    select(AnniversaryTag.tag_id).where(AnniversaryTag.anniv_id == anniv_id)
                )
            )
            .scalars()
            .all()
        )

        to_add, to_del = diff_sequence_data([i.id for i in tags if i.id], old_anniv_tag_ids)

        if to_del:
            await session.execute(delete(AnniversaryTag).where(AnniversaryTag.tag_id.in_(to_del)))
        if to_add:
            # 要判断tag表中是否已存在（id字段为空表示新增的记录）
            new_tag = await tag_repo.edit(
                session, create_by, [i for i in tags if not i.id], commit=False
            )
            if new_tag:
                to_add_data = [{"anniv_id": anniv_id, "tag_id": i["id"]} for i in new_tag]
                await session.run_sync(
                    lambda s: s.bulk_insert_mappings(AnnivMediaModel, to_add_data)
                )

        commit and await session.commit()

        return to_add_data

    async def add_media(self, session, anniv_id: str, media: List[UpdateMediaSchema], commit=True):
        new_media = await media_repo.edit(session, [i for i in media if not i.id], commit=False)
        media_ids = {i.id for i in media if i.id} | {i["id"] for i in new_media}

        to_add_data = [{"anniv_id": anniv_id, "media_id": tid} for tid in media_ids]
        await session.run_sync(lambda s: s.bulk_insert_mappings(AnnivMediaModel, to_add_data))

        commit and await session.commit()

    async def update_media(
        self, session, anniv_id: str, media: List[UpdateMediaSchema], commit=True
    ):
        old_anniv_media_ids = (
            await (
                session.execute(
                    select(AnnivMediaModel.media_id).where(AnnivMediaModel.anniv_id == anniv_id)
                )
            )
            .scalars()
            .all()
        )

        to_add, to_del = diff_sequence_data([i.id for i in media if i.id], old_anniv_media_ids)

        if to_del:
            await session.execute(
                delete(AnnivMediaModel).where(AnnivMediaModel.media_id.in_(to_del))
            )
        if to_add:
            # 要判断media表中是否已存在（id字段为空表示新增的记录）
            new_media = await media_repo.edit(session, [i for i in media if not i.id], commit=False)
            if new_media:
                to_add_data = [{"anniv_id": anniv_id, "media_id": i["id"]} for i in new_media]
                await session.run_sync(
                    lambda s: s.bulk_insert_mappings(AnnivMediaModel, to_add_data)
                )

        commit and await session.commit()

        return to_add_data


class RemindRepo(BaseMixin[ReminderRule]):
    async def add(
        self, session, anniv_id: str, user_ids: list[int], data: RemindRuleSchema, commit=True
    ):
        rules: list[ReminderRule] = []

        for uid in user_ids:
            rule = ReminderRule(
                anniv_id=anniv_id,
                user_id=uid,
                channels=data.channels,
                enabled=True,
            )

            # 给这条规则挂上多个 slot
            for cfg in data.slots:
                rule.slots.append(
                    ReminderSlot(
                        offset_days=cfg.offset_days,
                        trigger_time=cfg.trigger_time,
                        next_trigger_at=cfg.next_trigger_at,
                    )
                )

            rules.append(rule)
        session.add_all(rules)

        commit and await session.commit()
        return rules

    async def edit(
        self,
        session: AsyncSession,
        anniv_id: str,
        user_ids: list[int],
        data: RemindRuleSchema,
        commit=True,
    ):
        result = session.execute(self.filter(self.model.anniv_id == anniv_id)).scalars()
        for rule in result.scalars():
            await session.delete(rule)

        await self.add(session, anniv_id, user_ids, data, commit=False)
        commit and await session.commit()


tag_repo = TagRepo(TagModel)
anniv_member_repo = AnnivMemberRepo(AnniversaryMemberModel)
anniv_repo = AnnivRepo(AnniversaryModel)
remind_repo = RemindRepo(ReminderRule)
