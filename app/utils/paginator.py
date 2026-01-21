from typing import Any, Union, TypeVar, Generic, List

from sqlalchemy import Select, func
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy.ext.asyncio import AsyncSession


T = TypeVar("T")


class PaginatedResponse(BaseModel, Generic[T]):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    page: int
    limit: int
    total: int
    items: List[T] = Field(default_factory=list)


class CursorPaginatedResponse(BaseModel, Generic[T]):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    last: Any
    has_more: bool = False
    items: List[T] = Field(default_factory=list)


class Paginator:
    def __init__(self, db_session: AsyncSession):
        self.db = db_session

    async def paginate(
        self, stmt: Select, page: int, page_size: int = None, max_per_page=None
    ) -> PaginatedResponse:
        """分页查询"""
        if page_size is None:
            page_size = 20

        if page is None or page <= 0:
            raise ValueError("page or page size is None!")

        if max_per_page and page_size > max_per_page:
            raise ValueError("per page size exceeded the max limit!")

        offset = page_size * (page - 1)

        cnt_stmt = stmt.with_only_columns(func.count(), maintain_column_froms=True).order_by(None)

        ret = PaginatedResponse(
            items=(await self.db.execute(stmt.offset(offset).limit(page_size))).scalars().all(),
            total=(await self.db.execute(cnt_stmt)).scalar(),
            page=page,
            limit=page_size,
        )
        return ret


class ScrollPaginator(Paginator):
    """滚动分页（基于游标）"""

    def __init__(
        self,
        db_session: AsyncSession,
        stmt: Select,
        model,
        sort_col_index=None,
        order_col="id",
        custom_last_field=None,
    ):
        """

        :param query:
            查询对象
        :param model:
            排序字段所属model
        :param sort_col_index:
            排序字段的索引位置（query为多表join，返回的row对象元组由多个model组成）
            如：row([Post, PostCommunity])，现要根据post的id排序，则其索引下标为0
            注意：如果排序字段可直接通过row对象访问，则不用传递此参数，比如，row([Post, PostCommunity.community_id])，
                现要根据PostCommunity.community_id排序, 则无需传递此参数
        :param order_col: 排序字段名
        :param custom_last_field: 若指定custom_last_field，则last=model.custom_last_field；默认为model.order_col

        """
        super().__init__(db_session)
        self.stmt = stmt
        self.model = model
        self.data = []
        self.has_more = False
        self.last_score = None
        self.sort_col_index = sort_col_index
        self.order_col = order_col
        self.last_field = custom_last_field or order_col

    async def paginate(
        self,
        last_score: Union[str, int],
        limit: int = 20,
        max_limit: int = 100,
        is_reversed: bool = True,
    ) -> CursorPaginatedResponse:
        """
        基于游标分页

        :param last_score: 查询列表中最后一项的id
        :param max_limit: 最大分页限制
        :param limit: 滚动步长，使用limit+1用于判断是否还有更多数据
        :param is_reversed: 按时间倒序
        :return:
        """
        if limit < 1:
            raise ValueError("limit must >= 1")
        if max_limit and limit > max_limit:
            raise ValueError("per page size exceeded the max limit!")

        current_stmt = self.stmt
        if last_score:  # 非首次查询
            if is_reversed:
                current_stmt = current_stmt.where(getattr(self.model, self.order_col) < last_score)
            else:
                current_stmt = current_stmt.where(getattr(self.model, self.order_col) > last_score)

        result = await self.db.execute(current_stmt.limit(limit + 1))

        # 根据是否多表查询选择不同的解析方式
        if self.sort_col_index is not None:
            queryset = result.all()  # 多表join返回Row对象
        else:
            queryset = result.scalars().all()  # 单表返回模型对象

        if (length := len(queryset)) >= 1:
            if length > limit:
                self.data = queryset[:-1]
                last = queryset[-2]
                self.has_more = True
            else:
                self.data = queryset
                last = queryset[-1]

            if self.sort_col_index is None:
                self.last_score = getattr(last, self.last_field)
            else:
                self.last_score = getattr(last[self.sort_col_index], self.last_field)

        return CursorPaginatedResponse(
            last=self.last_score,
            has_more=self.has_more,
            items=self.data,
        )

    @property
    def last(self):
        return self.last_score

    @property
    def more(self):
        return self.has_more

    @property
    def total(self):
        return None
