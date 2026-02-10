from collections import defaultdict
from typing import List
from sqlalchemy import func, select
from app.constant import ResourceType, UserInterActionEnum
from app.models._mixin import BaseMixin
from app.models.action import UserInteraction
from app.schemas.action import DoInteractionSchema
from app.utils.dater import DT


class InteractionRepo(BaseMixin[UserInteraction]):
    async def get_like_collect_cnt(self, session, uid: int):
        stmt = (
            select(self.model.action, func.count(self.model.id).label("cnt"))
            .where(
                self.model.state == 1,
                self.model.uid == uid,
            )
            .group_by(self.model.action)
        )

        query = await session.execute(stmt)
        rows = query.all()

        ret = {"like_cnt": 0, "collect_cnt": 0}
        for r in rows:
            if r.action == UserInterActionEnum.LIKE:
                ret["like_cnt"] = r.cnt
            elif r.action == UserInterActionEnum.COLLECT:
                ret["collect_cnt"] = r.cnt

        return ret

    async def retrieve(
        self, session, action: UserInterActionEnum, uid: int, rtype: ResourceType, rid: str
    ):
        item = await self.filter_one(
            session,
            self.model.action == action,
            self.model.rtype == rtype,
            self.model.rid == rid,
            self.model.uid == uid,
        )
        return item

    async def retrieve_state(self, session, uid: int, rtype: ResourceType, rids: List[str]):
        ret = {rid: {} for rid in rids}

        if not rids:
            return ret

        base_cond = [self.model.rtype == rtype, self.model.uid == uid, self.model.rid.in_(rids)]

        stmt = select(self.model.rtype, self.model.rid, self.model.action, self.model.state).where(
            *base_cond
        )
        rows = (await session.execute(stmt)).all()

        for rtype, rid, action, state in rows:
            ret[rid][action] = state

        return ret

    async def add(
        self,
        session,
        *,
        action: UserInterActionEnum,
        uid: int,
        owner_uid: int,
        data: DoInteractionSchema,
    ):
        item = await self.create(
            session,
            {
                **data.model_dump(),
                "action": action,
                "uid": uid,
                "owner_uid": owner_uid,
            },
            commit=False,
        )

        return item


interaction_repo = InteractionRepo(UserInteraction)
