import time
from typing import List, Sequence

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.dialects.postgresql import insert as pg_insert

from app.constant import FollowState
from app.core.exception import APIException, ValidateError
from app.repo.relationship import fan_repo, follow_repo
from app.schemas.relationship import FollowItemSchema, QueryFollowSchema
from app.services.cache.user import UserStatCache
from app.utils.dater import DT


class RelationshipService:
    @staticmethod
    async def follow(session, from_uid: int, to_uid: int) -> None:
        if from_uid == to_uid:
            raise ValidateError("cannot follow yourself")

        now = DT.now_ts()
        body = {"from_uid": from_uid, "to_uid": to_uid, "state": FollowState.FOLLOWING, "now": now}
        follow_result = await follow_repo.edit(session, **body)
        fan_result = await fan_repo.edit(session, **body)

        await session.commit()

        if follow_result:
            await UserStatCache(from_uid).incr("follow_cnt")
        if fan_result:
            await UserStatCache(to_uid).incr("fan_cnt")

    @staticmethod
    async def unfollow(session, from_uid: int, to_uid: int) -> None:
        if from_uid == to_uid:
            raise ValidateError("cannot unfollow yourself")

        now = DT.now_ts()
        body = {"from_uid": from_uid, "to_uid": to_uid, "state": FollowState.UNFOLLOWED, "now": now}
        follow_result = await follow_repo.edit(session, **body)
        fan_result = await fan_repo.edit(session, **body)

        if follow_result:
            await UserStatCache(from_uid).decr("follow_cnt")
        if fan_result:
            await UserStatCache(to_uid).decr("fan_cnt")

    async def get_follow_state(
        self, session, from_uid: int, to_uids: List[int]
    ) -> dict[int, FollowState]:
        """
        获取关注状态
        :param to_uids: 专家id列表
        :return:
        """

        ret = await follow_repo.list_follow_state(session, from_uid, to_uids)

        return ret

    @staticmethod
    async def list_follow(session, uid: int, params: QueryFollowSchema):
        """获取关注列表"""
        paged = await follow_repo.list_follow(
            session, uid, params.last, params.limit, params.username
        )

        items = []
        for f, u in paged.items:
            i = FollowItemSchema(id=f.id, state=f.state, ctime=f.ctime, utime=f.utime, user=u)
            items.append(i)

        paged.items = items
        return paged

    @staticmethod
    async def list_fan(session, uid: int, params: QueryFollowSchema):
        paged = await fan_repo.list_fan(session, uid, params.last, params.limit, params.username)

        items = []
        for f, u in paged.items:
            i = FollowItemSchema(id=f.id, state=f.state, ctime=f.ctime, utime=f.utime, user=u)
            items.append(i)

        paged.items = items
        return paged
