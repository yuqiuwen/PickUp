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
    cursor = Column(BigInteger, nullable=False, default=0, comment="最新读取的游标")
    ttime = Column(Integer, nullable=False, comment="事件触发时间")
    ctime = Column(Integer, nullable=False, server_default=text("EXTRACT(EPOCH FROM now())::int"))


class SysNtfy(ULIDModel, TSModel):
    """系统通知"""

    __tablename__ = "sys_notification"

    __table_args__ = (Index("ix_notify_status_scheduled", "state", "scheduled_at"),)

    reminder_rule_id = Column(String(32), nullable=False, index=True, comment="提醒规则ID")
    scheduled_at = Column(
        DateTime(timezone=True), nullable=False, index=True, comment="计划发送时间"
    )
    sent_at = Column(DateTime(timezone=True), comment="实际发送时间")
    state = Column(SmallInteger, nullable=False, default=NtfyState.SCHEDULED, comment="NtfyState")

    provider = Column(String(32), nullable=False, comment="提供商, 如aliyun, twilio, smtp")
    provider_msg_id = Column(String(128), comment="提供商消息ID")
    error = Column(Text)
