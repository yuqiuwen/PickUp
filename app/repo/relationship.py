from collections import defaultdict
from typing import List
from sqlalchemy import func, select
from sqlalchemy.orm import Load, load_only
from app.constant import FollowState
from app.models._mixin import BaseMixin
from app.models.relationship import UserFan, UserFollow
from app.models.user import User
from app.repo.user import user_repo
from app.utils.dater import DT
from app.utils.paginator import ScrollPaginator


class FollowRepo(BaseMixin[UserFollow]):
    async def edit(self, session, from_uid: int, to_uid: int, state: FollowState, now: int):
        ret = await self.insert_do_update(
            session,
            {"from_uid": from_uid, "to_uid": to_uid, "ctime": now, "utime": now},
            index_elements=[self.model.from_uid, self.model.to_uid],
            _set={"state": state, "utime": now},
            commit=False,
        )

        return ret

    async def get_follow_cnt(self, session, uid: int):
        stmt = select(func.count()).where(
            self.model.state == FollowState.FOLLOWING,
            self.model.from_uid == uid,
        )
        ret = await session.execute(stmt)

        return ret.scalar()

    async def list_follow_state(self, session, from_uid: int, to_uids: List[int]):
        if not to_uids:
            return defaultdict(int)

        stmt = select(self.model.to_uid, self.model.state).where(
            self.model.from_uid == from_uid, self.model.to_uid.in_(to_uids)
        )
        rows = (await session.execute(stmt)).all()

        ret = defaultdict(int, {to_uid: state for to_uid, state in rows})
        return ret

    async def list_follow(self, session, uid: int, last=0, limit=20, username: str = None):
        cond = [self.model.state == FollowState.FOLLOWING, self.model.from_uid == uid]
        if username:
            cond.append(User.username.ilike(f"%{username}%"))

        stmt = (
            select(self.model, User)
            .select_from(self.model)
            .join(User, self.model.to_uid == User.id)
            .where(*cond)
            .options(Load(User).load_only(*user_repo.BASE_USER_COLS))
        )

        paged = await ScrollPaginator(session, stmt, self.model, sort_col_index=0).paginate(
            last, limit
        )

        return paged


class FanRepo(BaseMixin[UserFan]):
    async def edit(self, session, from_uid: int, to_uid: int, state: FollowState, now: int):
        ret = await self.insert_do_update(
            session,
            {"from_uid": from_uid, "to_uid": to_uid, "ctime": now, "utime": now},
            index_elements=[self.model.from_uid, self.model.to_uid],
            _set={"state": state, "utime": now},
            commit=False,
        )

        return ret

    async def get_fan_cnt(self, session, uid: int):
        stmt = select(func.count()).where(
            self.model.state == FollowState.FOLLOWING,
            self.model.to_uid == uid,
        )
        ret = await session.execute(stmt)

        return ret.scalar()

    async def list_fan(self, session, uid: int, last=0, limit=20, username: str = None):
        cond = [self.model.state == FollowState.FOLLOWING, self.model.to_uid == uid]
        if username:
            cond.append(User.username.ilike(f"%{username}%"))

        stmt = (
            select(self.model, User)
            .select_from(self.model)
            .join(User, self.model.from_uid == User.id)
            .where(*cond)
            .options(Load(User).load_only(*user_repo.BASE_USER_COLS))
        )

        paged = await ScrollPaginator(session, stmt, self.model).paginate(last, limit)

        return paged


follow_repo = FollowRepo(UserFollow)
fan_repo = FanRepo(UserFan)
