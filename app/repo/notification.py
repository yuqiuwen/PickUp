from collections import defaultdict
from sqlalchemy import Integer, and_, cast, desc, func, or_, select
from sqlalchemy.dialects.postgresql import aggregate_order_by, insert
from sqlalchemy.ext.asyncio import AsyncSession
from app.constant import (
    NtfyState,
    RemindActionEnum,
    SysActionEnum,
    SysAnnounceActionEnum,
)
from app.core.types import TActionEnum
from app.models._mixin import BaseMixin
from app.models.notification import RemindNtfy, RemindNtfyReadCursor, SysAnnounce, SysNtfy
from app.schemas.notification import (
    ACTION_FIELD_NAME_MAPPING,
    QueryRemindNotifySchema,
    UnReadMsgCntSchema,
)
from app.utils.dater import DT
from app.utils.paginator import ScrollPaginator


class RemindNotifyRepo(BaseMixin[RemindNtfy]):
    async def list(self, session: AsyncSession, to_uid: int, params: QueryRemindNotifySchema):
        """查询提醒通知
        按天聚合 取前2个用户
        id降序


        Args:
            session (AsyncSession): _description_
            to_uid (int): _description_
            params (QueryRemindNotifySchema): _description_
        """

        day_expr = func.date(func.to_timestamp(self.model.ttime))

        x_cond = [self.model.to_uid == to_uid, self.model.action.in_(params.actions)]

        cte = (
            select(
                self.model.id,
                self.model.from_uid,
                self.model.action,
                self.model.ttype,
                self.model.tid,
                self.model.ttime,
                self.model.ctime,
                day_expr.label("day"),
                func.row_number()
                .over(
                    partition_by=(
                        self.model.action,
                        self.model.ttype,
                        self.model.tid,
                        day_expr,
                        self.model.from_uid,
                    ),
                    order_by=self.model.id.desc(),
                )
                .label("rn"),
            )
            .where(*x_cond)
            .cte("cte")
        )

        x = select(cte).where(cte.c.rn == 1).cte("x")

        grouped = (
            select(
                func.max(x.c.id).label("id"),
                x.c.action,
                x.c.ttype,
                x.c.tid,
                (func.array_agg(aggregate_order_by(x.c.from_uid, x.c.id.desc()))[1:2]).label(
                    "from_uids"
                ),
                func.max(x.c.ttime).label("ttime"),
                func.max(x.c.ctime).label("ctime"),
                func.count().label("user_total"),
                func.count().label("total"),  # 去重后 count == distinct from_uid 数
            )
            .select_from(x)
            .group_by(x.c.action, x.c.ttype, x.c.tid, x.c.day)
        )

        sq = grouped.subquery()
        stmt = select(sq).order_by(sq.c.id.desc())

        paged = await ScrollPaginator(session, stmt, sq.c, order_col="id", is_row=True).paginate(
            params.last, params.limit, max_limit=100
        )

        return paged

    async def _get_unread_count(self, session, to_uid, last_read_map: dict[RemindActionEnum, int]):
        conditions = [
            and_(self.model.action == action, self.model.id > last_read_map[action])
            for action in RemindActionEnum.mappings()
        ]
        stmt = (
            select(self.model.action, func.count(self.model.id))
            .where(self.model.to_uid == to_uid, or_(*conditions))
            .group_by(self.model.action)
        )

        rows = (await session.execute(stmt)).all()

        return {action: count for action, count in rows}

    async def get_lastest_id(self, session, to_uid, max_ctime: int = None):
        cond = [self.model.to_uid == to_uid]
        if max_ctime:
            cond.append(self.model.ctime <= max_ctime)
        stmt = (
            select(self.model.action, func.max(self.model.id))
            .where(*cond)
            .group_by(self.model.action)
        )

        rows = (await session.execute(stmt)).all()
        return {a: max_id for a, max_id in rows}


class SysNotifyRepo(BaseMixin[SysNtfy]):
    async def list(self, session: AsyncSession, to_uid: int, params: QueryRemindNotifySchema):
        stmt = select(self.model).where(self.model.to_uid == to_uid).order_by(self.model.id.desc())
        paged = await ScrollPaginator(session, stmt, self.model).paginate(
            params.last, params.limit, max_limit=100
        )

        return paged

    async def _get_unread_count(
        self,
        session,
        to_uid,
        last_id: int,
    ):
        if not last_id:
            return 0

        stmt = select(func.count(self.model.id)).where(self.model.id > last_id)

        cnt = (await session.execute(stmt)).scalar_one_or_none()

        return cnt or 0

    async def get_lastest_id(self, session, to_uid, max_ctime: int = None):
        cond = [self.model.to_uid == to_uid]
        if max_ctime:
            cond.append(self.model.ctime <= max_ctime)

        stmt = select(self.model.id).where(*cond).order_by(self.model.id.desc()).limit(1)

        ret = (await session.execute(stmt)).scalar()
        return ret or 0


class AnnounceNotifyRepo(BaseMixin[SysAnnounce]):
    async def list(self, session: AsyncSession, params: QueryRemindNotifySchema):
        stmt = (
            select(self.model)
            .where(self.model.state == NtfyState.SENT)
            .order_by(self.model.id.desc())
        )
        paged = await ScrollPaginator(session, stmt, self.model).paginate(
            params.last, params.limit, max_limit=100
        )

        return paged

    async def _get_unread_count(
        self,
        session,
        to_uid,
        last_id: int,
    ):
        if not last_id:
            return 0

        stmt = select(func.count(self.model.id)).where(
            self.model.id > last_id, self.model.state == NtfyState.SENT
        )

        cnt = (await session.execute(stmt)).scalar_one_or_none()

        return cnt or 0

    async def get_lastest_id(self, session, max_ctime: int = None):
        cond = [self.model.state == 1]
        if max_ctime:
            cond.append(self.model.ctime <= max_ctime)

        stmt = select(self.model.id).where(*cond).order_by(self.model.id.desc()).limit(1)

        result = (await session.execute(stmt)).scalar()
        return result or 0


class RemindNtfyCursorRepo(BaseMixin[RemindNtfyReadCursor]):
    async def edit(self, session, to_uid: int, data: dict[TActionEnum, int]):
        now = DT.now_ts()
        values = [
            {"to_uid": to_uid, "action": int(action), "cursor": int(max_id), "utime": now}
            for action, max_id in data.items()
            if max_id and max_id > 0
        ]
        if not data:
            return

        if values:
            ins = insert(RemindNtfyReadCursor).values(values)
            stmt = ins.on_conflict_do_update(
                index_elements=[RemindNtfyReadCursor.to_uid, RemindNtfyReadCursor.action],
                set_={
                    "cursor": func.greatest(RemindNtfyReadCursor.cursor, ins.excluded.cursor),
                    "utime": now,
                },
            )

            await session.execute(stmt)
            await session.commit()
            return

    async def get_last_read(self, session, to_uid: int) -> dict[TActionEnum, int]:
        stmt = select(self.model.action, self.model.cursor).where(self.model.to_uid == to_uid)

        rows_map = (await session.execute(stmt)).all()

        return defaultdict(int, {action: cursor for action, cursor in rows_map})

    async def get_unread_count(self, session, to_uid: int):
        # 上一次读取的游标map
        last_read_map = await self.get_last_read(session, to_uid)

        remind_ntfy_unread = await remind_ntfy_repo._get_unread_count(
            session, to_uid, last_read_map
        )

        sys_ntfy_unread = await sys_ntfy_repo._get_unread_count(
            session, to_uid, last_read_map[SysActionEnum.SYS]
        )

        announce_ntfy_unread = await announce_ntfy_repo._get_unread_count(
            session, to_uid, last_read_map[SysAnnounceActionEnum.ANNOUNCE]
        )

        result = {
            ACTION_FIELD_NAME_MAPPING[action]: count for action, count in remind_ntfy_unread.items()
        }

        result[ACTION_FIELD_NAME_MAPPING[SysActionEnum.SYS]] = sys_ntfy_unread
        result[ACTION_FIELD_NAME_MAPPING[SysAnnounceActionEnum.ANNOUNCE]] = announce_ntfy_unread

        return UnReadMsgCntSchema(**result)


remind_ntfy_repo = RemindNotifyRepo(RemindNtfy)
sys_ntfy_repo = SysNotifyRepo(SysNtfy)
announce_ntfy_repo = AnnounceNotifyRepo(SysAnnounce)

remind_ntfy_cursor_repo = RemindNtfyCursorRepo(RemindNtfyReadCursor)
