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


class UserRole(EnumPro):
    SUPER = "super", "超级管理员"
    ADMIN = "admin", "管理员"
    USER = "user", "用户"


class RepeatType(IntEnumPro):
    "重复类型"

    NONE = 0, "不重复"
    YEARLY = 1, "每年"
    MONTHLY = 2, "每月"
    WEEKLY = 3, "每周"


class ReminderChannel(IntEnumPro):
    "提醒渠道"

    SITE = 1, "站内信"
    EMAIL = 2, "邮件"
    SMS = 3, "短信"


class NotificationStatus(IntEnumPro):
    SCHEDULED = 0, "待发送"
    SENT = 1, "已送达"
    FAILED = 2, "失败"
    CANCELED = 3, "已取消"


class AttachmentType(IntEnumPro):
    IMAGE = 1, "图片"
    VIDEO = 2, "视频"
    FILE = 3, "文件"
    LINK = 4, "链接"


class CalendarType(IntEnumPro):
    """日历类型"""

    GREGORIAN = 1, "公历"
    LUNAR = 2, "农历"


class GroupRole(IntEnumPro):
    """共享组角色"""

    OWNER = 1, "所有者"
    MEMBER = 2, "成员"


class SettingsType(IntEnumPro):
    """系统设置类型"""

    SWITCH = 1, "开关"
    SELECT = 2, "选项"
    INPUT = 3, "输入"


class SettingsGroup(EnumPro):
    """系统设置类型"""

    ACCOUNT = 1, "账号设置"
    GENERIC = 2, "通用设置"
    NOTIFICATION = 3, "通知设置"
    PRIVACY = 4, "隐私设置"
    OTHER = 5, "其他"


class SettingsSwitch(EnumPro):
    """系统设置开关值"""

    ON = "ON", "开启"
    OFF = "OFF", "关闭"


class InviteState(IntEnumPro):
    """邀请状态"""

    PENDING = 0, "待接受"
    ACCEPTED = 1, "已接受"
    REJECTED = 2, "已拒绝"
    EXPIRED = 3, "已过期"
    CANCELLED = 4, "已撤销"


class InviteTargetType(IntEnumPro):
    """邀请目标类型"""

    ANNIVERSARY = 1, "纪念日"
    GROUP = 2, "共享组"


class NtfyState(IntEnumPro):
    """通知状态"""

    SCHEDULED = 0, "待发送"
    SENT = 1, "已送达"
    FAILED = 2, "发送失败"
    CANCELED = 3, "已取消"
