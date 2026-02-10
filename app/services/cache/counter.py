from typing import List, Literal
from app.database import redcache
from app.services.cache import BaseCache, CacheKey


AnnivCounterField = Literal["collect_cnt", "like_cnt", "share_cnt", "comment_cnt"]


class AnnivCounter(BaseCache):
    __KEY__ = CacheKey.COUNTER_ANNIV.value

    def __init__(self, anniv_id: str):
        self.key = self.__KEY__.format(anniv_id)

    async def get(self):
        return await redcache.hgetall(self.key)

    async def expire(self, ex=3600 * 24 * 3):
        return await redcache.expire(self.key, ex)

    @classmethod
    async def get_many(cls, ids: List[str]):
        if not ids:
            return {}

        async with redcache.pipeline() as pipe:
            for rid in ids:
                pipe.hgetall(cls.__KEY__.format(rid))

            rows = await pipe.execute()

            result = {id: {k: int(v) for k, v in d.items()} for id, d in zip(ids, rows)}

            return result

    async def add(self, data: dict, ex=3600 * 24 * 3):
        async with redcache.pipeline() as pipe:
            pipe.hset(self.key, mapping=data).expire(self.key, ex)
            ret = await pipe.execute()
            return ret[0]

    async def delete(self):
        return await redcache.delete(self.key)

    async def exists(self):
        return await redcache.exists(self.key)

    async def incr(self, field: AnnivCounterField, amount=1):
        """
        :param field: redis hash计数字段的field
        :param amount: 数量，支持符号位
        :return:
        """

        cnt = await redcache.script.hincr_if_exists(keys=[self.key], args=[field, amount])
        if cnt is None or cnt >= 0:
            return cnt

        cnt = await redcache.script.hincr_if_exists(keys=[self.key], args=[field, -cnt])
        return cnt

    async def scan(self, count=5000):
        return await redcache.scan_uk(self.key, count=count)
