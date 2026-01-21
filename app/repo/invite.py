from typing import Sequence

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.constant import InviteState, InviteTargetType
from app.models._mixin import BaseMixin
from app.models.invite import InviteModel


class InviteRepo(BaseMixin[InviteModel]):
    async def add(self, session, data: dict, commit=True):
        item = await self.create(session, data, commit=commit)
        return item

    async def batch_add(self, session, data: list[dict], commit=True):
        item = await self.batch_create(session, data, commit=commit)
        return item

    async def list(
        self,
        session: AsyncSession,
        ttype: InviteTargetType = None,
        tid: str = None,
        state: InviteState | list[InviteState] | None = None,
        expires_at_range: Sequence[None | int] = None,
    ) -> list[InviteModel]:
        cond = []
        if ttype is not None:
            cond.append(self.model.ttype == ttype)
        if tid:
            cond.append(self.model.tid == tid)
        if state is not None:
            if isinstance(state, list):
                cond.append(self.model.state.in_(state))
            else:
                cond.append(self.model.state == state)
        if expires_at_range is not None:
            min_expires_at, max_expires_at = expires_at_range
            if min_expires_at is not None:
                cond.append(self.model.expires_at >= min_expires_at)
            if max_expires_at is not None:
                cond.append(self.model.expires_at <= max_expires_at)

        stmt = self.filter(*cond)
        ret = await session.execute(stmt).scalars().all()

        return ret

    async def retrieve(self, session, invite_id: str = None, token: str = None) -> InviteModel:
        cond = []
        if invite_id is not None:
            cond.append(InviteModel.id == invite_id)
        if token:
            cond.append(InviteModel.token == token)
        item = await self.first_or_404(session, *cond, _with_for_update=True)
        return item


invite_repo = InviteRepo(InviteModel)
