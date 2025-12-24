from enum import IntEnum, Enum


class EnumPro(Enum):
    def __new__(cls, value, desc):
        obj = object.__new__(cls)
        obj._value_ = value
        obj.desc = desc
        return obj

    @classmethod
    def mappings(cls):
        return {c._value_: c.desc for c in cls}

    @classmethod
    def options(cls):
        return [{"name": c.desc, "value": c.value} for c in cls]


class IntEnumPro(IntEnum):
    def __new__(cls, value, desc):
        obj = int.__new__(cls, value)
        obj._value_ = value
        obj.desc = desc
        return obj

    @classmethod
    def mappings(cls):
        return {c._value_: c.desc for c in cls}

    @classmethod
    def options(cls):
        return [{"name": c.desc, "value": c.value} for c in cls]


class UserType(IntEnum):
    NORMAL = 1


class AuthType(IntEnumPro):
    PHONE = 1, "手机号"
    ACCOUNT = 2, "账号"
    EMAIL = 3, "邮箱"
    WX = 4, "微信"


class SMSSendBiz(EnumPro):
    """短信发送业务场景"""

    LOGIN = "login", "登录"
    SIGN = "sign", "注册"
    SET_PWD = "set_pwd", "设置密码"
    BIND_PHONE = "bind_phone", "绑定手机号"
    REVOKE = "revoke", "注销"
