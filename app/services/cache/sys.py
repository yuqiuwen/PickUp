from app.constant import SMSSendBiz
from app.core.exception import AuthException
from app.database import redcache
from . import BaseCache, CacheKey


class AvatarCache(BaseCache):
    """头像缓存"""

    __KEY__ = CacheKey.DEFAULT_AVATAR.value

    def __init__(self):
        self.key = self.__KEY__

    async def get(self):
        return await redcache.lrange(self.key, 0, -1)

    async def add(self, data: list, expire=3600 * 24 * 30):
        ret = await redcache.lpush(self.key, *data)
        return ret

    async def delete(self):
        return await redcache.delete(self.key)

    async def exists(self):
        return await redcache.exists(self.key)


class VerifyCodeCache(BaseCache):
    """验证码缓存"""

    __KEY__ = CacheKey.VERIFY_PHONE_CODE.value

    def __init__(self, biz: SMSSendBiz, phone: str):
        if not phone:
            raise ValueError("phone or email can not be null")
        self.key = self.__KEY__.format(biz.value, phone)
        self.phone = phone

    async def get(self):
        return await redcache.get(self.key)

    async def add(self, code: str, expire=600):
        if not code:
            raise ValueError("code can not be null")
        return await redcache.setex(self.key, 600, code)

    async def delete(self):
        return redcache.delete(self.key)

    async def exists(self):
        return await redcache.exists(self.key)

    async def validate(self, code: str, is_delete=True):
        """
        :param code:
        :param is_delete: 验证成功后是否删除验证码
        :return:
        """
        cache_code = await self.get()
        if not code or not cache_code or code != cache_code:
            raise AuthException(errmsg="验证码错误")
        if is_delete:
            await self.delete()
        return code
