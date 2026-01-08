from app.constant import CalendarType, GroupRole, RepeatType
from app.models.module import *


class AnniversaryModel(ULIDModel, TSModel, BigOperatorModel, StateModel):
    """纪念日"""

    __tablename__ = "anniversary"
    __table_args__ = (Index("idx_state_uid_date", "state", "owner_id", "event_date"),)

    name = Column(String(50), nullable=False, comment="纪念日名称")
    description = Column(String(100), comment="描述")
    event_date = Column(Date, nullable=False, comment="纪念日日期")
    event_time = Column(DateTime, nullable=False, comment="纪念日时间")
    calendar_type = Column(
        SmallInteger, nullable=False, default=CalendarType.GREGORIAN, comment="日历类型"
    )
    share_mode = Column(SmallInteger, nullable=False, default=0, comment="0独享 1共享")
    owner_id = Column(BigInteger, nullable=False, comment="纪念日归属者ID，拥有该纪念日所有权")
    is_reminder = Column(Boolean, nullable=False, default=False, comment="是否提醒")
    repeat_type = Column(SmallInteger, nullable=False, default=RepeatType.NONE, comment="重复类型")

    owner = relationship(
        "User",
        lazy="joined",
        viewonly=True,
        uselist=False,
        primaryjoin="AnniversaryModel.owner_id == foreign(User.id)",
    )


class AnniversaryMemberModel(TSModel, BigOperatorModel):
    """纪念日成员"""

    __tablename__ = "anniversary_member"
    __table_args__ = (UniqueConstraint("anniv_id", "ttype", "tid", name="uq_anniv_member_dedup"),)

    anniv_id = Column(String(32), primary_key=True, comment="纪念日ID")
    ttype = Column(SmallInteger, primary_key=True, comment="目标类型 1 group 2 member")
    tid = Column(String(32), primary_key=True, comment="目标对象ID，可以是group或member")
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
    __table_args__ = (
        UniqueConstraint(
            "anniv_id",
            "user_id",
            "channel",
            "days_before",
            "trigger_time",
            name="uq_reminder_rule_dedup",
        ),
        Index("ix_reminder_enabled_next", "enabled", "next_trigger_at"),
    )

    anniv_id = Column(String(32), nullable=False, index=True, comment="纪念日ID")
    user_id = Column(BigInteger, nullable=False, index=True, comment="用户ID")
    channel = Column(SmallInteger, nullable=False, comment="ReminderChannel")
    days_before = Column(Integer, nullable=False, default=0)
    trigger_time = Column(Time, nullable=False)  # e.g. 09:00

    enabled = Column(Boolean, nullable=False, default=True)

    # 由调度任务维护，便于扫描
    next_trigger_at = Column(DateTime(timezone=True), index=True)
