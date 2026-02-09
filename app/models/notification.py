from app.constant import NtfyState
from app.models.base import BaseBigModel
from app.models.module import *


class RemindNtfy(BaseBigModel):
    """提醒类通知，包括：点赞、收藏、关注、邀请"""

    __tablename__ = "notification_remind"
    __table_args__ = (Index("notification_remind_to_uid_action", "to_uid", "action"),)

    from_uid = Column(BigInteger, nullable=False, comment="触发者")
    to_uid = Column(BigInteger, nullable=False, comment="送达者")
    action = Column(SmallInteger, nullable=False, comment="行为类型：`ActionEnum`")
    ttype = Column(SmallInteger, nullable=False, comment="ResourceType目标对象资源类型")
    tid = Column(String, nullable=False, comment="目标对象id")
    ttime = Column(Integer, nullable=False, comment="事件触发时间")
    ctime = Column(Integer, nullable=False, server_default=text("EXTRACT(EPOCH FROM now())::int"))


class SysNtfy(BaseBigModel):
    """
    系统通知
    """

    __tablename__ = "sys_notification"

    __table_args__ = (Index("ix_sys_notify_to_uid_action", "to_uid", "action"),)

    title = Column(String, nullable=False)
    content = Column(Text)
    to_uid = Column(BigInteger, nullable=False, comment="送达者")
    action = Column(SmallInteger, nullable=False, comment="行为类型：`ActionEnum`")
    ttype = Column(SmallInteger, nullable=False, comment="ResourceType目标对象资源类型")
    tid = Column(String, nullable=False, comment="目标对象id")
    ttime = Column(Integer, nullable=False, comment="事件触发时间")
    ctime = Column(Integer, nullable=False, server_default=text("EXTRACT(EPOCH FROM now())::int"))


class SysAnnounce(BaseBigModel, TSModel):
    """
    系统公告

    target_users:
        all
        vip
        new
    """

    __tablename__ = "sys_announce"

    __table_args__ = (Index("ix_sys_announce_state", "state"),)

    title = Column(String, nullable=False)
    content = Column(Text, nullable=False)
    state = Column(SmallInteger, nullable=False, default=1)
    target_users = Column(ARRAY(String(50)), comment="目标用户")


class RemindNtfyReadCursor(Base):
    """通知读取游标（包含系统通知）"""

    __tablename__ = "notification_remind_cursor"

    to_uid = Column(BigInteger, nullable=False, primary_key=True, comment="送达者")
    action = Column(
        SmallInteger, nullable=False, primary_key=True, comment="行为类型：`ActionEnum`"
    )
    cursor = Column(BigInteger, nullable=False, default=0, comment="最新读取的游标")
    utime = Column(
        Integer,
        nullable=False,
        onupdate=lambda: int(time.time()),
        server_default=text("EXTRACT(EPOCH FROM now())::int"),
    )
