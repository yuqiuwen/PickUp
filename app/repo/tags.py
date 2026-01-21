from typing import List
from app.models.module import *
from app.models.tags import TagModel
from app.schemas.common import UpdateMediaSchema


class TagRepo(BaseMixin[TagModel]):
    async def list(self, session, name: str):
        stmt = select(self.model.id, self.model.name).where(self.model.name.ilike(f"%{name}%"))
        ret = (await session.execute(stmt)).all()

        return ret

    async def batch_add(self, session, create_by: int, names: List[str]):
        ret = await self.insert_or_ignore(
            session, [{"name": n, "create_by": create_by} for n in names]
        )
        return ret


tag_repo = TagRepo(TagModel)
