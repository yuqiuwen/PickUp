from app.models._mixin import BaseMixin
from app.models.user import User


class UserRepo(BaseMixin[User]):
    async def create_user(self, session, commit=True, **data):
        user = await self.create(session, data, commit=commit)
        return user

    async def get_by_cond(self, session, cond: list):
        return await self.filter_one(session, *cond)

    async def get_or_404(self, session, pk):
        return await self.first_or_404(session, self.model.id == pk)


user_repo: UserRepo = UserRepo(User)
