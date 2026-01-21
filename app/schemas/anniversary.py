from datetime import date, datetime, time, timedelta
from typing import List, Literal
from zoneinfo import ZoneInfo
from dateutil.relativedelta import relativedelta
from pydantic import BaseModel, Field, condate, field_validator, model_validator
from sqlalchemy.sql.expression import true
from app.constant import AnniversaryType, CalendarType, ReminderChannel, RepeatType
from app.core.exception import ValidateError
from app.schemas.field import AutoFormatTimeField, TimestampField
from app.schemas.common import CursorPageQueryModel, EntityModel, OrderByModel, UpdateMediaSchema
from app.schemas.user import ShareGroupMemberSchema, ShareGroupShema, SimpleUser, UserSchema
from app.utils.common import parse_sort_str
from app.utils.dater import DT


class CreateTagSchema(BaseModel):
    id: str | None = Field(default=None)
    name: str


class InviteFieldSchema(BaseModel):
    """
    {
        "invite_external_users": [{"account": "name@example.com", "account_type": "email"}],
        "invite_app_users": [10000001, 10000002],
        "invite_groups": ["group_id1", "group_id2"],
        "message": "加入这个纪念日"
    }
    """

    invite_external_users: list[dict] = Field(
        default_factory=list, description="邀请未注册的外部用户"
    )
    invite_app_users: list[int] = Field(default_factory=list, description="邀请app用户id")
    invite_groups: list[str] = Field(default_factory=list, description="邀请共享组id")
    message: str = Field(max_length=100)


class RemindConfig(BaseModel):
    offset_days: int = Field(description="负数表示提前，正数表示未来，0表示当天")
    trigger_time: time
    next_trigger_at: datetime | None = Field(default=None, description="下次触发时间")


class RemindRuleSchema(BaseModel):
    channels: list[ReminderChannel]
    slots: list[RemindConfig]


class CreateAnnivSchema(BaseModel):
    """纪念日"""

    name: str = Field(min_length=2, max_length=20, description="纪念日名称")
    description: str = Field(default=None, description="描述")
    event_date: date = Field(description="纪念日日期")
    event_year: int = Field(default=None, description="纪念日年份")
    event_time: time | None = Field(default=None, description="纪念日时间")
    cover: str = Field(default=None, description="封面")
    calendar_type: CalendarType = Field(default=CalendarType.GREGORIAN, description="日历类型")
    type: AnniversaryType = Field(default=AnniversaryType.ANNIVERSARY, description="纪念日类型")
    share_mode: Literal[0, 1] = Field(default=0, description="共享模式, 0独享 1共享")
    owner_id: int = Field(default=None, description="纪念日归属者ID")
    is_reminder: bool = Field(default=True, description="是否提醒")
    email_remind: bool = Field(default=True, description="是否开启邮件提醒")
    repeat_type: RepeatType = Field(default=RepeatType.YEARLY, description="重复类型")
    lunar_year: int | None = Field(default=None)
    lunar_month: int | None = Field(default=None)
    lunar_day: int | None = Field(default=None)
    lunar_is_leap: bool = Field(default=False)
    tz: str | None = Field(default="Asia/Shanghai")

    next_trigger_at: int | None = Field(default=None)

    share: InviteFieldSchema | None = Field(default=None, description="共享配置")
    remind_rule: RemindRuleSchema | None = Field(default=None, description="提醒配置")
    media: list[UpdateMediaSchema] | None = Field(default=None, min_length=1, max_length=10)
    tags: list[CreateTagSchema] | None = Field(default=None, max_length=10)

    # 核心验证：处理时间默认值并检查日期一致性、计算下一次触发时间
    @model_validator(mode="after")
    def validate_data(self) -> "CreateAnnivSchema":
        from app.utils.remind_calculator import RemindConfigCalculator

        calculator = RemindConfigCalculator(ZoneInfo(self.tz))

        if self.calendar_type == CalendarType.LUNAR:
            _calc_event_date = date(self.lunar_year, self.lunar_month, self.lunar_day)
        else:
            _calc_event_date = self.event_date

        self.event_year = self.event_date.year

        if self.type == AnniversaryType.BIRTHDAY:
            self.repeat_type = RepeatType.YEARLY

        # calcaute next trigger time
        _trigger_time = self.event_time or time(
            hour=0,
            minute=0,
            second=0,
            microsecond=0,
        )

        # 日程的下一次发生时间
        next_trigger = calculator.calculate_next_trigger(
            RemindConfig(offset_days=0, trigger_time=_trigger_time),
            _calc_event_date,
            self.repeat_type,
            self.calendar_type,
            self.lunar_is_leap,
        )
        self.next_trigger_at = next_trigger

        if self.remind_rule and self.remind_rule.slots:
            # 去重
            slot_sets = {(i.offset_days, i.trigger_time) for i in self.remind_rule.slots}
            self.remind_rule.slots = []

            for offset_days, trigger_time in slot_sets:
                slot = RemindConfig(offset_days=offset_days, trigger_time=trigger_time)
                slot.next_trigger_at = calculator.calculate_next_trigger(
                    remind_config=slot,
                    event_date=_calc_event_date,
                    repeat_type=self.repeat_type,
                    calendar_type=self.calendar_type,
                    is_leap=self.lunar_is_leap,
                )

                self.remind_rule.slots.append(slot)

        return self


class AnnivMemberSchema(EntityModel):
    groups: list[ShareGroupShema] = Field(default_factory=list)
    users: list[UserSchema] = Field(default_factory=list)


class AnnivSchema(EntityModel):
    id: str
    name: str
    description: str | None
    event_year: int
    event_date: date
    event_time: time | None
    cover: str | None
    calendar_type: int
    type: int
    is_reminder: bool
    lunar_year: int | None = Field(default=None)
    lunar_month: int | None = Field(default=None)
    lunar_day: int | None = Field(default=None)
    lunar_is_leap: bool
    next_trigger_at: datetime
    tz: str

    members: list[AnnivMemberSchema]
    owner: UserSchema


class AnnivStat(BaseModel):
    year_total: int = Field(default=0)
    share_total: int = Field(default=0)
    next_anniv: AnnivSchema | None = Field(default=None)


class QueryAnnivSchema(BaseModel):
    name: str | None = Field(default=None)
    event_year: int | None = Field(default=None)
    event_date: date | None = Field(default=None)
    type: AnniversaryType | str | None = Field(default=None)
    share_mode: Literal[0, 1] | None = Field(default=None, description="共享模式, 0独享 1共享")
    is_reminder: bool | None = Field(default=None)

    order_by: str | None = Field(
        default="event_date.desc", description="event_date.asc event_date.desc"
    )

    @field_validator("order_by", mode="after")
    @classmethod
    def parse_order_by(cls, value: str) -> str:
        if value:
            if value == "default":
                return value
            return parse_sort_str(value)


class AnnivStats(BaseModel):
    like_cnt: int = 0
    collect_cnt: int = 0
    comment_cnt: int = 0


class Interaction(BaseModel):
    is_like: int = 0
    is_collect: int = 0


class AnnivFeedItem(EntityModel):
    id: str
    name: str
    description: str | None = Field(default=None)
    event_year: int
    event_date: date
    event_time: time | None = Field(default=None)
    cover: str | None = Field(default=None)
    calendar_type: CalendarType
    share_mode: int
    type: AnniversaryType
    is_reminder: bool
    tz: str
    lunar_year: int | None = Field(default=None)
    lunar_month: int | None = Field(default=None)
    lunar_day: int | None = Field(default=None)
    lunar_is_leap: bool
    next_trigger_at: datetime
    ctime: int
    utime: int

    owner: UserSchema
    stats: AnnivStats = Field(default_factory=AnnivStats)
    interaction: Interaction = Field(default_factory=Interaction)
