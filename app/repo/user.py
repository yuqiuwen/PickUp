from app.models._mixin import BaseMixin
from app.models.user import User


"""
repo methods:
create/add
update/edit
delete/remove
get/retrieve
"""


class UserRepo(BaseMixin[User]):
    async def add(self, session, commit=True, **data):
        user = await self.create(session, data, commit=commit)
        return user

    async def get_by_cond(self, session, cond: list):
        return await self.filter_one(session, *cond)

    async def retrieve_or_404(self, session, pk):
        return await self.first_or_404(session, self.model.id == pk)

    async def edit(self, session, pk, data, commit=True):
        user = await self.retrieve_or_404(session, pk)
        user = await self.update(session, user, data, commit=commit)
        return user


user_repo: UserRepo = UserRepo(User)
