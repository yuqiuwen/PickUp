from typing import List
from fastapi import HTTPException
from sqlalchemy import func
from app.constant import ResourceType, UserInterActionEnum

from app.repo.anniversary import anniv_repo
from app.repo.interaction import interaction_repo
from app.schemas.action import DoInteractionSchema
from app.schemas.anniversary import AnnivStats
from app.services.cache.counter import AnnivCounter, AnnivCounterField
from app.utils.dater import DT


class InteractionService:
    ANNIV_COUNTER_NAME_MAP = {
        UserInterActionEnum.COLLECT: "collect_cnt",
        UserInterActionEnum.LIKE: "like_cnt",
        UserInterActionEnum.SHARE: "share_cnt",
        UserInterActionEnum.COMMENT: "comment_cnt",
    }

    def __init__(self, action: UserInterActionEnum, rtype: ResourceType):
        self.action = action
        self.rtype = rtype

    @property
    def _anniv_counter_name(self):
        return self.ANNIV_COUNTER_NAME_MAP[self.action]

    @staticmethod
    async def check_anniv_exist(session, rid):
        return await anniv_repo.retrieve_or_404(session, rid)

    async def get_resource(self, session, rid):
        if self.rtype == ResourceType.ANNIV:
            return await self.check_anniv_exist(session, rid)

    async def update_anniv_counter(self, session, anniv_id: str, amount: int):
        cache = AnnivCounter(anniv_id)
        if not await cache.exists():
            data = await anniv_repo.get_counter(session, anniv_id)
            data[self._anniv_counter_name] += amount
            await cache.add(data)

            return 1

        return await cache.incr(self._anniv_counter_name, amount)

    async def update_counter(self, session, rid: str, amount: int):
        if self.rtype == ResourceType.ANNIV:
            await self.update_anniv_counter(session, rid, amount)

    async def create_interaction(self, session, uid: int, data: DoInteractionSchema):
        r = await self.get_resource(session, data.rid)
        if not r:
            raise HTTPException(404)

        delta = 0
        item = await interaction_repo.retrieve(session, self.action, uid, data.rtype, data.rid)
        if not item:
            if data.state == 1:
                await interaction_repo.add(
                    session, action=self.action, uid=uid, owner_uid=r.create_by, data=data
                )
                delta = 1
            else:
                delta = 0
        else:
            if data.state == item.state:
                delta = 0
            else:
                item.owner_uid = r.create_by
                item.utime = DT.now_ts()
                item.state = data.state
                delta = 1 if data.state == 1 else -1

        await session.commit()

        if delta != 0:
            await self.update_counter(session, data.rid, delta)

        return 1

    @staticmethod
    async def get_interaction_state(session, uid: int, rtype: ResourceType, rids: str | List[str]):
        if not rids:
            return
        ret = await interaction_repo.retrieve_state(session, uid, rtype, rids)

        return ret
