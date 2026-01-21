from typing import List
from app.ext.jwt import TokenUserInfo
from app.repo.tags import tag_repo
from app.schemas.common import TagsSchema


class TagService:
    async def list_tag(session, search: str) -> list[TagsSchema]:
        data = await tag_repo.list(session, search)

        return data

    async def add_tag(session, cur_use: TokenUserInfo, names: List[str]):
        await tag_repo.batch_add(session, cur_use.id, names)

        return
