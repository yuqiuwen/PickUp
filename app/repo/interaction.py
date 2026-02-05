from sqlalchemy import func, select
from app.constant import UserInterActionEnum
from app.models._mixin import BaseMixin
from app.models.action import UserInteraction


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


interaction_repo = InteractionRepo(UserInteraction)
