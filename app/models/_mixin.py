from typing import Generic, List, Dict, Union, Literal, Sequence, Mapping
import time

from sqlalchemy.ext.asyncio import AsyncSession
from ulid import ULID
from sqlalchemy import (
    delete,
    func,
    text,
    select,
    Column,
    Integer,
    String,
    BigInteger,
    SmallInteger,
    update,
    TIMESTAMP,
)
from sqlalchemy.orm import joinedload, defer, selectinload, declared_attr, exc, relationship
from sqlalchemy.dialects.postgresql import insert
from fastapi import HTTPException

from app.core.types import Model


class BaseMixin(Generic[Model]):
    def __init__(self, model: type[Model]):
        self.model = model

    def columns(self):
        return [c.name for c in self.model.__table__.columns]

    async def get(self, session: AsyncSession, pk):
        ret = await session.execute(select(self.model).where(self.model.id == pk))
        return ret.scalar_one_or_none()

    async def get_or_404(self, session: AsyncSession, pk):
        ret = await self.get(session, pk)
        if not ret:
            raise HTTPException(status_code=404)
        return ret

    def filter(self, *cond):
        stmt = select(self.model).where(*cond)
        return stmt

    async def filter_one(self, session: AsyncSession, *cond):
        ret = await session.execute(select(self.model).where(*cond))
        return ret.scalars().first()

    async def query_update(self, session: AsyncSession, *, cond: Sequence, data: dict, commit=True):
        """
        更新数据库中的数据
        :param session: 数据库会话
        :param cond: 条件
        :param data: 新数据
        :return: 更新行数
        """

        stmt = update(self.model).where(*cond).values(**data)
        ret = await session.execute(stmt)
        commit and await session.commit()
        return ret.rowcount

    async def first_or_404(self, session: AsyncSession, *cond, _with_for_update=False):
        stmt = select(self.model).where(*cond)

        if _with_for_update:
            stmt = stmt.with_for_update()

        ret = (await session.execute(stmt)).scalar_one_or_none()

        if not ret:
            raise HTTPException(status_code=404)
        return ret

    async def create(self, session: AsyncSession, data: dict, commit=True, **kwargs):
        instance = self.model(**data)
        await self.save(session, instance, commit=commit)
        return instance

    async def batch_create(self, session: AsyncSession, data: List[Dict], commit=True):
        if not data:
            return 0
        ret = await session.run_sync(lambda s: s.bulk_insert_mappings(self.model, data))
        await session.flush()
        if commit:
            await session.commit()

        return ret

    async def batch_update(
        self,
        session: AsyncSession,
        values: List[Dict],
        commit=True,
        handle_unmatch: Literal["raise", "abort", "ignore"] = "abort",
    ):
        try:
            await session.run_sync(lambda s: s.bulk_update_mappings(self.model, values))
            await session.flush()
            if commit:
                await session.commit()
        except exc.StaleDataError as e:
            if handle_unmatch == "raise":
                raise e
            elif handle_unmatch == "abort":
                raise HTTPException(404, detail="批量更新失败，数据不存在！")
            else:
                pass

    async def update(
        self, session: AsyncSession, instance: Model, data: dict, commit=True, **kwargs
    ):
        for attr, value in data.items():
            setattr(instance, attr, value)
        await self.save(session, instance, commit=commit)
        return instance

    async def save(self, session: AsyncSession, instance: Model, commit=True):
        try:
            session.add(instance)
            await session.flush()
            if commit:
                await session.commit()
        except Exception as e:
            await session.rollback()
            raise e
        else:
            return instance

    async def delete(self, session: AsyncSession, *cond, commit=True):
        ret = await delete(self.model).where(*cond)
        await session.flush()
        if commit:
            await session.commit()
        return ret

    async def delete_instance(self, session: AsyncSession, instance: Model, commit=True):
        ret = await session.delete(instance)
        await session.flush()
        if commit:
            await session.commit()
        return ret

    async def insert_or_ignore(
        self,
        session: AsyncSession,
        data: Union[Mapping, Sequence],
        returning: Sequence | Model = None,
        constraint=None,
        index_elements=None,
        index_where=None,
        commit=True,
    ):
        if returning is not None and not isinstance(data, (Mapping, Sequence)):
            returning = None

        stmt = (
            insert(self.model)
            .values(data)
            .on_conflict_do_nothing(constraint, index_elements, index_where)
        )
        if returning:
            if isinstance(returning, Sequence):
                stmt = stmt.returning(*returning)
            else:
                stmt = stmt.returning(returning)

        ret = await session.execute(stmt)
        if returning:
            if isinstance(data, Mapping):
                ret = ret.first()
                ret = ret and ret[0]
            else:
                ret = ret.all()
        else:
            ret = ret.rowcount

        await session.flush()
        if commit:
            await session.commit()
        return ret

    async def insert_do_update(
        self,
        session: AsyncSession,
        data: Union[Mapping, Sequence],
        constraint=None,
        index_elements: list = None,
        index_where: tuple = None,
        where=None,
        returning: Union[tuple, list] = None,
        commit=True,
    ):
        """
        :param session:
        :param data: 更新数据字典，支持批量插入，若为批量插入，每条记录的key必须一致，不能缺失
        :param constraint: 唯一约束
        :param index_elements: 唯一约束, `constraint` 和 `index_elements`只能传递其中一个参数
        :param index_where: 更细粒度控制唯一约束，当满足唯一约束和index_where条件的才会触发更新
        :param where: 基于表级数据的过滤
        :param returning: 返回值
        :param commit:
        :return: 若有returning且插入单个记录，返回对应属性；否则返回rowcount
        """
        try:
            if isinstance(data, Mapping):
                stmt = insert(self.model).values(**data)
                set_ = data
            else:
                stmt = insert(self.model).values(data)
                set_ = {c: getattr(stmt.excluded, c) for c in data[0].keys()}

            do_update_stmt = stmt.on_conflict_do_update(
                constraint=constraint,
                index_elements=index_elements,
                index_where=index_where,
                set_=set_,
                where=where,
            )
            if returning:
                do_update_stmt = do_update_stmt.returning(*returning)

            ret = await session.execute(do_update_stmt)
            if returning:
                if isinstance(data, Mapping):
                    ret = ret.first()
                    ret = ret and ret[0]
                else:
                    ret = ret.all()
            else:
                ret = ret.rowcount

            await session.flush()
            if commit:
                await session.commit()

            return ret

        except Exception as e:
            await session.rollback()
            raise e

    @classmethod
    async def execute_sql(
        cls, session: AsyncSession, sql: str, *, params: dict = None, query_one: bool = False
    ) -> Union[dict, list[dict]]:
        sql = text(sql)
        cursor_result = await session.execute(sql, params)
        if query_one:
            return cursor_result.mappings().one() or None
        return cursor_result.mappings().all() or []
