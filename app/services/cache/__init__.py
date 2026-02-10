from abc import abstractmethod, ABC
from enum import unique, Enum
from typing import Iterable, Literal

from redis import StrictRedis


@unique
class CacheKey(Enum):
    TOKEN = "token:{}"  # session_id: {session_id}
    DEFAULT_AVATAR = "default_avatar"  # 默认头像
    VERIFY_PHONE_CODE = "verify_code:{}:{}"  # 验证码: {业务标识}:{手机号或三方账号}
    USER_STAT = "user_stat:{}"  # 用户统计：{用户id}
    UNREAD_MSG_CNT = "unread_msg_counter:{}"  # 用户未读消息计数：{用户id}
    JWT_TOKEN = "jwt_token:{}:{}:{}-{}"  # JWT令牌：{app_name}:{token类型}:{user_id}-{jti}

    COUNTER_ANNIV = "counter_anniv:{}"  # {anniv_id}


class BaseCache(ABC):
    @property
    @abstractmethod
    def __KEY__(self):
        pass

    @abstractmethod
    async def get(self, *args, **kwargs):
        pass

    @abstractmethod
    async def delete(self, *args, **kwargs):
        pass

    @abstractmethod
    async def add(self, *args, **kwargs):
        pass

    @staticmethod
    async def get_cache_data(
        client: StrictRedis,
        data_type: Literal["string", "hash"],
        keys: Iterable,
        *,
        cmd=None,
        cmd_args=None,
        cmd_options=None,
        sep_rule=None,
        pk_name="id",
    ):
        """
        获取缓存数据

        :param client: redis client
        :param data_type: redis值类型：string单值类型，hash映射类型
        :param cmd: redis命令
        :param cmd_args: redis命令参数
        :param cmd_options: redis命令参数
        :param sep_rule: key分隔规则（为了获取id），从右向左分隔，元组3个元素分别表示：分隔字符、最大分隔次数、截取结果索引。
            如(":", 1, 1)表示 按 `:` 从右至左分隔，最多分隔1次，取分隔结果的索引下标1
        :param keys:
        :param pk_name:
        :return: 单值类型返回嵌套元组，hash类型返回嵌套字典
        """
        if not cmd_args:
            cmd_args = ()
        if not cmd_options:
            cmd_options = {}

        async def check_key(_key):
            ret = await client.execute_command(cmd, _key, *cmd_args, **cmd_options)
            if (_id := _key.rsplit(sep_rule[0], sep_rule[1])[sep_rule[2]]) == "None":
                return
            return _id, ret

        if data_type == "string":
            data = []
            for key in keys:
                r = await check_key(key)
                if r is None:
                    continue
                data.append((r[1]))
            return data

        elif data_type == "hash":
            data = []
            for key in keys:
                r = await check_key(key)
                if r is None:
                    continue

                data.append({pk_name: r[0], **r[1]})
            return data
