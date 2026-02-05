from abc import abstractmethod, ABC
from enum import unique, Enum


@unique
class CacheKey(Enum):
    TOKEN = "token:{}"  # session_id: {session_id}
    DEFAULT_AVATAR = "default_avatar"  # 默认头像
    VERIFY_PHONE_CODE = "verify_code:{}:{}"  # 验证码: {业务标识}:{手机号或三方账号}
    USER_STAT = "user_stat:{}"  # 用户统计：{用户id}
    UNREAD_MSG_CNT = "unread_msg_counter:{}"  # 用户未读消息计数：{用户id}
    JWT_TOKEN = "jwt_token:{}:{}:{}-{}"  # JWT令牌：{app_name}:{token类型}:{user_id}-{jti}


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
