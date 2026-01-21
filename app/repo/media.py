from app.models.module import *
from app.models.sys import MediaModel
from app.schemas.common import UpdateMediaSchema


class MediaRepo(BaseMixin[MediaModel]):
    async def edit(self, session, data: list[UpdateMediaSchema], commit=True) -> list[dict]:
        """更新media

        Returns:
            list[dict]: 新增的media
        """
        data = [{"type": item.type, "path": item.path} for item in data]
        items = await self.insert_or_ignore(
            session,
            data,
            index_elements=["path"],
            returning=(self.model.id, self.model.path),
            commit=commit,
        )

        return [{"id": item.id, "path": item.path} for item in items]


media_repo = MediaRepo(MediaModel)
