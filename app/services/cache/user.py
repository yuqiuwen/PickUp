from typing import Literal, TypeAlias
from app.config import settings
from app.repo.interaction import interaction_repo
from app.repo.relationship import fan_repo, follow_repo
from app.schemas.notification import EmptyUnReadMsgCnt, UnReadMsgCntSchema
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

UnReadMsgCntField: TypeAlias = Literal[
    "sys_cnt", "fan_cnt", "like_cnt", "collect_cnt", "comment_cnt", "invite_cnt"
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


class UnReadMsgCntCache(BaseCache):
    __KEY__ = CacheKey.UNREAD_MSG_CNT.value

    def __init__(self, uid: int):
        self.key = self.__KEY__.format(uid)

    async def add(self, data: dict, exp=24 * 60 * 60):
        async with redcache.pipeline() as pipe:
            pipe.hset(self.key, mapping=data).expire(self.key, exp)
            ret = await pipe.execute()
            return ret[0]

    async def get(self):
        ret = await redcache.hgetall(self.key)
        if ret:
            return UnReadMsgCntSchema(**ret)

    async def delete(self):
        return await redcache.delete(self.key)

    @property
    async def exists(self):
        return await redcache.exists(self.key)

    async def incr(self, field: UnReadMsgCntField):
        """
        计数 +1
        :param field:
        :return:
        """
        return await redcache.script.hincr_if_exists(keys=[self.key], args=[field, 1], amount=1)

    async def decr(self, field: UnReadMsgCntField, amount=1):
        """
        计数 -1
        :param field:
        :param amount: 减少的数量
        :return:
        """
        cnt = await redcache.script.hincr_if_exists(keys=[self.key], args=[field, -amount])
        if cnt is None or cnt >= 0:
            return cnt

        cnt = await redcache.script.hincr_if_exists(keys=[self.key], args=[field, -cnt])
        return cnt

    async def reset_all(self):
        """重置全部消息为：已读"""
        if self.exists:
            await self.add(EmptyUnReadMsgCnt)
            return EmptyUnReadMsgCnt

    async def reset_one(self, field: UnReadMsgCntField):
        """重置某一类消息"""
        if self.exists:
            return await redcache.hset(self.key, field, 0)
