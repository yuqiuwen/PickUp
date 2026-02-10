from enum import IntEnum, Enum
from types import MappingProxyType


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
    DAILY = 4, "每天"
    HALF_YEARLY = 11, "每半年"
    THREE_MONTHLY = 23, "每3个月"


class ReminderChannel(IntEnumPro):
    "提醒渠道"

    SITE = 1, "站内信"
    EMAIL = 2, "邮件"
    SMS = 3, "短信"


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


class SettingsGroup(EnumPro):
    """系统设置分组"""

    ACCOUNT = "account", "账号设置"
    GENERIC = "generic", "通用设置"
    NOTIFICATION = "notification", "通知设置"
    PRIVACY = "privacy", "隐私设置"
    OTHER = "other", "其他"


class SettingsSwitch(EnumPro):
    """系统设置开关值"""

    ON = "ON", "开启"
    OFF = "OFF", "关闭"


class InviteState(IntEnumPro):
    """邀请状态"""

    PENDING = 0, "待发送"
    SENT = 1, "已发送"
    ACCEPTED = 2, "已接受"
    DECLINED = 3, "已拒绝"
    EXPIRED = 4, "已过期"
    CANCELLED = 5, "已撤销"


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


class AnniversaryType(IntEnumPro):
    """纪念日类型"""

    ANNIVERSARY = 1, "纪念日"
    BIRTHDAY = 2, "生日"
    BACKWARD = 3, "倒数日"


class MediaType(IntEnumPro):
    """媒体类型"""

    IMAGE = 1, "图片"
    VIDEO = 2, "视频"
    FILE = 3, "文件"
    LINK = 4, "链接"
    AUDIO = 5, "音频"


class MediaState(IntEnumPro):
    """媒体状态"""

    UNREVIEWED = -1, "待审核"
    FAILED = 0, "审核失败"
    PASSED = 1, "审核通过"


class RemindActionEnum(IntEnumPro):
    LIKE = 1, "点赞"
    COLLECT = 2, "收藏"
    COMMENT = 3, "评论"
    REPLY = 4, "回复"
    MENTION = 5, "提及"
    FAN = 6, "粉丝"
    INVITE = 7, "邀请"

    REFUSED_INVITE = -7, "拒绝邀请"


class SysActionEnum(IntEnumPro):
    SYS = 99, "系统"


class SysAnnounceActionEnum(IntEnumPro):
    ANNOUNCE = 98, "公告"


class ResourceType(IntEnumPro):
    ANNIV = 1, "纪念日"
    NOTES = 2, "笔记"
    COMMENT = 3, "评论"


class EmailBizEnum(EnumPro):
    VERIFY_CODE_SIGN = (
        "verify_code_sign",
        "注册验证码",
    )
    VERIFY_CODE_LOGIN = (
        "verify_code_login",
        "登录验证码",
    )
    VERIFY_CODE_SET_PWD = (
        "verify_code_reset_pwd",
        "重置密码验证码",
    )
    VERIFY_CODE_BIND_PHONE = (
        "verify_code_bind_phone",
        "绑定手机号验证码",
    )
    VERIFY_CODE_REVOKE = (
        "verify_code_account_revoke",
        "账号注销验证码",
    )

    INVITE_ANNIV = "invite_anniv", "纪念日邀请"
    INVITE_GROUP = "invite_group", "共享组邀请"


class CommentState(IntEnumPro):
    ENABLED = 1, "启用"
    DELETED = 0, "删除"
    DISABLED = -1, "隐藏"


class UserInterActionEnum(IntEnumPro):
    LIKE = 1, "点赞"
    COLLECT = 2, "收藏"
    SHARE = 3, "分享"
    COMMENT = 4, "评论"


class FollowState(IntEnumPro):
    UNFOLLOWED = 0, "取消关注"
    FOLLOWING = 1, "关注"
    MUTUAL = 2, "相互关注"
