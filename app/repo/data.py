from app.models._mixin import BaseMixin
from app.models.data import RelayPostRecords
from app.utils.paginator import Paginator, ScrollPaginator


class PostRepo(BaseMixin[RelayPostRecords]):
    async def list_server_asset(self, session, page=1, limit=20, post_key: str = None):
        stmt = self.filter(self.model.post_key == post_key)
        paged = await Paginator(session).paginate(stmt, page, limit)

        return paged


post_repo: PostRepo = PostRepo(RelayPostRecords)
