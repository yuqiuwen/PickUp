from typing import List
from app.models.module import *
from app.models.tags import TagModel
from app.schemas.anniversary import CreateTagSchema
from app.schemas.common import UpdateMediaSchema


class TagRepo(BaseMixin[TagModel]):
    async def list(self, session, *, name: str = None, ids: List[str] = None):
        cond = [self.model.state == 1]
        if name:
            cond.append(self.model.name.ilike(f"%{name}%"))
        if ids:
            cond.append(self.model.id.in_(ids))
        stmt = select(self.model.id, self.model.name).where(*cond)
        ret = (await session.execute(stmt)).all()

        return ret

    async def batch_add(self, session, create_by: int, names: List[str]):
        ret = await self.insert_or_ignore(
            session, [{"name": n, "create_by": create_by} for n in names]
        )
        return ret

    async def edit(
        self, session, create_by: int, data: List[CreateTagSchema], commit=True
    ) -> List[dict]:
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


tag_repo = TagRepo(TagModel)
