from app.constant import CalendarType, GroupRole, RepeatType
from app.models.module import *


"""
创建 anniversary
写入 anniversary_member：owner 一条（role=OWNER）
若 owner_reminder.enabled=true：为 owner 写入 reminder_rule（默认提醒共享成员和共享组，包括owner自己）
若 share_mode=1：生成 invite 并发邮件（对 group：给组内成员逐个发 invite，或只给组成员生成 invite 记录）
"""


class AnniversaryModel(ULIDModel, TSModel, BigOperatorModel, StateModel):
    """纪念日"""

    __tablename__ = "anniversary"
    __table_args__ = (Index("ix_state_uid_date", "state", "owner_id", "event_date"),)

    name = Column(String(50), nullable=False, comment="纪念日名称")
    description = Column(Text, comment="描述")
    event_year = Column(Integer, nullable=False, comment="纪念日年份")
    event_date = Column(Date, nullable=False, comment="纪念日日期")
    event_time = Column(Time(timezone=False), comment="纪念日时间")
    tz = Column(String(64), nullable=False, default="Asia/Shanghai")
    cover = Column(String(255), comment="封面")
    calendar_type = Column(
        SmallInteger, nullable=False, default=CalendarType.GREGORIAN, comment="日历类型"
    )
    type = Column(SmallInteger, nullable=False, comment="纪念日类型 AnniversaryType")
    share_mode = Column(SmallInteger, nullable=False, default=0, comment="0独享 1共享")
    owner_id = Column(BigInteger, nullable=False, comment="纪念日归属者ID，拥有该纪念日所有权")
    is_reminder = Column(Boolean, nullable=False, default=False, comment="是否提醒")
    repeat_type = Column(SmallInteger, nullable=False, default=RepeatType.NONE, comment="重复类型")
    location = Column(String(100), comment="地点")

    # LUNAR
    lunar_year = Column(Integer, nullable=True)
    lunar_month = Column(SmallInteger, nullable=True)
    lunar_day = Column(SmallInteger, nullable=True)
    lunar_is_leap = Column(Boolean, nullable=True, default=False, comment="是否闰月")

    next_trigger_at = Column(
        DateTime(timezone=True), nullable=False, index=True, comment="下一次触发时间"
    )

    user = relationship(
        "User",
        lazy="joined",
        viewonly=True,
        uselist=False,
        primaryjoin="AnniversaryModel.create_by == foreign(User.id)",
    )

    owner = relationship(
        "User",
        lazy="joined",
        viewonly=True,
        uselist=False,
        primaryjoin="AnniversaryModel.owner_id == foreign(User.id)",
    )


class AnniversaryMemberModel(ULIDModel, TSModel):
    """纪念日成员"""

    __tablename__ = "anniversary_member"
    __table_args__ = (
        UniqueConstraint("anniv_id", "ttype", "tid", name="uq_anniversary_member_anniv_idttypetid"),
    )

    anniv_id = Column(String(32), nullable=False, comment="纪念日ID")
    ttype = Column(SmallInteger, nullable=False, comment="目标类型 1 group 2 member")
    tid = Column(String(32), nullable=False, comment="目标对象ID，可以是group或member")
    role = Column(SmallInteger, nullable=False, default=GroupRole.MEMBER, comment="角色GroupRole")
    joined_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())


class AnniversaryTag(Base):
    """纪念日标签"""

    __tablename__ = "anniversary_tag"

    anniv_id = Column(String(32), nullable=False, primary_key=True, comment="纪念日ID")
    tag_id = Column(String(32), nullable=False, primary_key=True, comment="标签ID")


# 提醒规则（用户维度）
class ReminderRule(ULIDModel, TSModel):
    __tablename__ = "reminder_rule"
    __table_args__ = (UniqueConstraint("anniv_id", "user_id"),)

    anniv_id = Column(String(32), nullable=False, index=True, comment="纪念日ID")
    user_id = Column(BigInteger, nullable=False, index=True, comment="用户ID")
    channels = Column(ARRAY(SmallInteger), nullable=False, comment="ReminderChannel列表")
    enabled = Column(Boolean, nullable=False, default=True)

    slots = relationship(
        "ReminderSlot",
        cascade="all, delete-orphan",
        primaryjoin="ReminderRule.id == foreign(ReminderSlot.rule_id)",
    )


class ReminderSlot(ULIDModel, TSModel):
    """具体提醒配置"""

    __tablename__ = "reminder_slot"
    __table_args__ = (
        UniqueConstraint("rule_id", "offset_days", "trigger_time", name="uq_reminder_slot_dedup"),
    )

    rule_id = Column(String(32), comment="提醒规则ID")
    offset_days = Column(
        Integer, nullable=False, default=0, comment="负数代表提前, 正数代表推后, 0表示当天"
    )
    trigger_time = Column(Time, nullable=False)  # e.g. 09:00:00
    next_trigger_at = Column(DateTime(timezone=True), comment="下次触发时间")


class AnnivMediaModel(TSModel):
    """纪念日媒体资源"""

    __tablename__ = "anniversary_media"

    anniv_id = Column(String(32), primary_key=True, comment="纪念日ID")
    media_id = Column(String(32), primary_key=True, comment="媒体ID")
    sort = Column(SmallInteger, nullable=False, default=1, comment="排序号")
