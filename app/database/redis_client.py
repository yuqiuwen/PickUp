from dataclasses import dataclass
import sys
import traceback
from typing import Any

from redis.asyncio import StrictRedis
from redis.exceptions import AuthenticationError, TimeoutError
import redis_lock
from contextlib import contextmanager

from app.config import settings
from app.core.loggers import app_logger

LUA_HINCR_IF_EXISTS = """
if redis.call('HEXISTS', KEYS[1], ARGV[1]) == 1 then
  return redis.call('HINCRBY', KEYS[1], ARGV[1], ARGV[2])
else
  return nil
end
"""


LUA_INCR_IF_EXISTS = """
if redis.call('EXISTS', KEYS[1]) == 1 then
  return redis.call('INCRBY', KEYS[1], ARGV[1])
else
  return nil
end
"""


LUA_HSET_IF_EXISTS = """
if redis.call('HEXISTS', KEYS[1], ARGV[1]) == 1 then
  return redis.call('HSET', KEYS[1], ARGV[1], ARGV[2])
else
  return nil
end
"""


@dataclass
class Script:
    hincr_if_exists: callable = None
    incr_if_exists: callable = None
    hset_if_exists: callable = None


class RedisX:
    def __init__(self, prefix="REDIS", **kwargs):
        """
        :param app: flask app
        :param prefix: the prefix of redis url, ex: `REDIS_CACHE`, `REDIS_LOCK`. Default, as `REDIS`
        :param kwargs:
        """
        self.prefix = prefix
        self._redis_client: StrictRedis | None = None
        self.script = Script()

    async def init_app(self, **kwargs):
        kwargs.update(decode_responses=True)
        name = f"{self.prefix}_URL"
        redis_url = getattr(settings, name, None)
        if not redis_url:
            raise RuntimeError(f"Redis URL is not set for {name}")
        kwargs.update(
            socket_timeout=settings.REDIS_TIMEOUT,
            socket_connect_timeout=settings.REDIS_TIMEOUT,
        )
        self._redis_client = StrictRedis.from_url(redis_url, **kwargs)
        self.register_scripts()
        await self.open()
        return self

    @property
    def client(self) -> StrictRedis:
        return self._redis_client

    def __getattr__(self, name: str) -> Any:
        return getattr(self.client, name)

    def __getitem__(self, name):
        return self.client[name]

    def __setitem__(self, name, value):
        self.client[name] = value

    def __delitem__(self, name):
        del self.client[name]

    def register_scripts(self):
        self.script.hincr_if_exists = self.client.register_script(LUA_HINCR_IF_EXISTS)
        self.script.incr_if_exists = self.client.register_script(LUA_INCR_IF_EXISTS)
        self.script.hset_if_exists = self.client.register_script(LUA_HSET_IF_EXISTS)

    def lock(self, name, expire=None, id=None, signal_expire=1000, auto_renewal=False):
        return redis_lock.Lock(
            self.client, name, expire, id, auto_renewal, signal_expire=signal_expire
        )

    async def open(self) -> None:
        """触发初始化连接"""
        try:
            await self.client.ping()
        except TimeoutError:
            app_logger.error("redis连接超时")
            sys.exit()
        except AuthenticationError:
            app_logger.error("redis连接认证失败")
            sys.exit()
        except Exception as e:
            traceback.print_exc()
            app_logger.error(f"redis连接异常 {e}")
            sys.exit()
        else:
            app_logger.info(f"初始化 {self.prefix} 成功")

    async def aclose(self) -> None:
        if self.client:
            await self.client.aclose()

    @contextmanager
    def acquire_lock(
        self,
        name,
        expire=None,
        id=None,
        signal_expire=1000,
        auto_renewal=False,
        blocking=False,
        timeout=None,
        raise_not_acquire=False,
    ):
        _lock = self.lock(
            name, expire=expire, id=id, signal_expire=signal_expire, auto_renewal=auto_renewal
        )
        is_acquire = False
        try:
            is_acquire = _lock.acquire(blocking=blocking, timeout=timeout)
        except Exception as e:
            if raise_not_acquire:
                raise e
            pass

        try:
            yield is_acquire
        finally:
            is_acquire and _lock and _lock.locked() and _lock.release()

    async def scan_uk(self, pattern, count=None):
        """使用scan command匹配keys并去重"""
        seen = set()

        kwargs = {"match": pattern}
        if count is not None:
            kwargs["count"] = count
        async for key in self.client.scan_iter(**kwargs):
            if key in seen:
                continue
            seen.add(key)
            yield key

    async def delete_prefix(self, prefix: str) -> int:
        """
        删除指定前缀的所有 key

        :param prefix: 前缀
        :return:
        """
        keys = await self.scan_uk(f"{prefix}*")
        if keys:
            return await self.client.delete(*keys)
        return 0


redcache = RedisX(prefix="REDIS_CACHE")  # 业务缓存
pms_cache = RedisX(prefix="REDIS_PMS")  # 权限缓存
redis_socket = RedisX(prefix="REDIS_SOCKET")  # socket专用


async def init(enable_cache=True, enable_pms_cache=True, enable_redis_socket=True):
    if enable_cache:
        await redcache.init_app()
    if enable_pms_cache:
        await pms_cache.init_app()
    if enable_redis_socket:
        await redis_socket.init_app()


async def aclose():
    await redcache.aclose()
    await pms_cache.aclose()
    await redis_socket.aclose()
