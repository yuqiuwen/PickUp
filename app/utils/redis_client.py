from dataclasses import dataclass

import redis
import redis_lock
from contextlib import contextmanager

from app.config import settings

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
        self._redis_client = None
        self.script = Script()

    def init_app(self, **kwargs):
        kwargs.update(decode_responses=True)
        name = f"{self.prefix}_URL"
        redis_url = getattr(settings, name, None)
        if not redis_url:
            raise RuntimeError(f"Redis URL is not set for {name}")
        self._redis_client = redis.StrictRedis.from_url(redis_url, **kwargs)
        self.register_scripts()

    @property
    def client(self):
        return self._redis_client

    def __getattr__(self, name):
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

    def scan_uk(self, pattern, count=None):
        """使用scan command匹配keys并去重"""
        uq_keys = set()
        for key in self.client.scan_iter(match=pattern, count=count):
            if key not in uq_keys:
                uq_keys.add(key)
                yield key
