from app.config import settings
from . import BaseCache, CacheKey
from app.database import pms_cache


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
