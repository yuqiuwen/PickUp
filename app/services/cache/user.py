from typing import Literal, TypeAlias
from app.config import settings
from app.repo.interaction import interaction_repo
from app.repo.relationship import fan_repo, follow_repo
from app.schemas.user import UserStats
from . import BaseCache, CacheKey
from app.database import pms_cache, redcache


UserStatsField: TypeAlias = Literal[
    "follow_cnt",
    "fan_cnt",
    "like_cnt",
    "collect_cnt",
    "comment_cnt",
]


class TokenCache(BaseCache):
    __KEY__ = CacheKey.TOKEN.value

    def __init__(self, session_id):
        self.key = self.__KEY__.format(session_id)

    async def get(self):
        return await pms_cache.get(self.key)

    async def add(self, data: str, expire):
        ret = await pms_cache.set(self.key, data, ex=expire)
        return ret

    async def delete(self):
        return await pms_cache.delete(self.key)

    async def exists(self):
        return await pms_cache.exists(self.key)


class JWTTokenCache(BaseCache):
    __KEY__ = CacheKey.JWT_TOKEN.value

    def __init__(self, token_type, user_id, jti):
        """
        {app_name}:{token_type}:{user_id}-{jti}
        app_name: 应用名称
        token_type: 令牌类型，access 或 refresh
        user_id: 用户ID
        jti: jti
        """

        self.key = self.__KEY__.format(settings.APP_NAME, token_type, user_id, jti)

    async def get(self):
        return await pms_cache.get(self.key)

    async def add(self, data: str, expire):
        # data: sub
        ret = await pms_cache.set(self.key, data, ex=expire)
        return ret

    async def delete(self):
        return await pms_cache.delete(self.key)

    async def exists(self):
        return await pms_cache.exists(self.key)

    async def delete_prefix(self):
        return await pms_cache.delete_prefix(self.key)


class UserStatCache(BaseCache):
    """用户统计属性缓存，如：关注数、粉丝数"""

    __KEY__ = CacheKey.USER_STAT.value

    def __init__(self, uid: int):
        self.uid = uid
        self.key = self.__KEY__.format(uid)

    async def get(self, session):
        ret = await redcache.hgetall(self.key)
        if ret:
            return UserStats(**ret)

        follow_cnt = await follow_repo.get_follow_cnt(session, self.uid)
        fan_cnt = await fan_repo.get_fan_cnt(session, self.uid)
        like_collect_cnt_mapping = await interaction_repo.get_like_collect_cnt(session, self.uid)

        # TODO comment

        data = {"follow_cnt": follow_cnt, "fan_cnt": fan_cnt, **like_collect_cnt_mapping}
        await self.add(data)

        ret = UserStats(**data)
        return ret

    async def add(self, data: dict, expire=12 * 60 * 60):
        async with redcache.pipeline() as pipe:
            pipe.hset(self.key, mapping=data).expire(self.key, expire)
            ret = await pipe.execute()
            return ret[0]

    async def delete(self):
        return await redcache.delete(self.key)

    async def exists(self):
        return await redcache.exists(self.key)

    async def incr(self, field: UserStatsField):
        """
        计数 +1
        :param field:
        :return:
        """
        return await redcache.script.hincr_if_exists(keys=[self.key], args=[field, 1])

    async def decr(self, field: UserStatsField):
        """
        计数 -1
        :param field:
        :return:
        """
        cnt = await redcache.script.hincr_if_exists(keys=[self.key], args=[field, -1])
        if cnt is None or cnt >= 0:
            return cnt

        cnt = await redcache.script.hincr_if_exists(keys=[self.key], args=[field, -cnt])
        return cnt
