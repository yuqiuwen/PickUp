from datetime import datetime, date, time, timedelta
from zoneinfo import ZoneInfo
from dateutil.relativedelta import relativedelta
from app.constant import CalendarType, RepeatType
from app.schemas.anniversary import RemindConfig
from app.utils.dater import DT
from lunar_python import Lunar, Solar


class RemindConfigCalculator:
    """提醒时间计算器 - 使用 lunar_python"""

    def __init__(self, timezone: ZoneInfo = None):
        if not timezone:
            timezone = DT.tz()
        self.tz = timezone

    def calculate_next_trigger(
        self,
        remind_config: "RemindConfig",
        event_date: date,
        repeat_type: "RepeatType",
        calendar_type: "CalendarType",
        is_leap=False,
    ) -> datetime | None:
        """计算下一次触发时间"""
        now = datetime.now(self.tz)
        today = now.date()

        # Step 1: 找到下一个纪念日
        next_anniv = self._get_next_anniversary(
            event_date, repeat_type, calendar_type, today, is_leap
        )

        if next_anniv is None:
            return None

        # Step 2: 计算触发时间
        next_trigger = self._build_trigger_datetime(
            next_anniv, remind_config.offset_days, remind_config.trigger_time
        )

        # Step 3: 如果已过期，找下一个周期
        if next_trigger <= now:
            if repeat_type == RepeatType.NONE:
                return None

            next_anniv = self._get_next_anniversary(
                event_date, repeat_type, calendar_type, next_anniv + timedelta(days=1), is_leap
            )
            if next_anniv is None:
                return None

            next_trigger = self._build_trigger_datetime(
                next_anniv, remind_config.offset_days, remind_config.trigger_time
            )

        return next_trigger

    def _build_trigger_datetime(
        self, anniversary_date: date, offset_days: int, trigger_time: time
    ) -> datetime:
        """构建触发时间"""
        remind_date = anniversary_date + timedelta(days=offset_days)
        return datetime.combine(remind_date, trigger_time, tzinfo=self.tz)

    # ============ 纪念日日期计算 ============

    def _get_next_anniversary(
        self,
        event_date: date,
        repeat_type: "RepeatType",
        calendar_type: "CalendarType",
        reference_date: date,
        is_leap=False,
    ) -> date | None:
        """获取下一个纪念日日期（公历）"""

        if repeat_type == RepeatType.NONE:
            if calendar_type == CalendarType.LUNAR:
                solar = self._lunar_to_solar(
                    event_date.year, event_date.month, event_date.day, is_leap
                )
                return solar if solar and solar >= reference_date else None
            return event_date if event_date >= reference_date else None

        if calendar_type == CalendarType.LUNAR:
            return self._next_lunar_anniversary(event_date, repeat_type, reference_date, is_leap)
        else:
            return self._next_gregorian_anniversary(event_date, repeat_type, reference_date)

    # ============ 公历计算 ============

    def _next_gregorian_anniversary(
        self, event_date: date, repeat_type: "RepeatType", reference_date: date
    ) -> date:
        """计算公历纪念日的下一个日期"""
        delta = self._get_repeat_delta(repeat_type)
        next_date = event_date

        # 快速跳跃优化
        if repeat_type == RepeatType.YEARLY and reference_date.year > event_date.year:
            years_diff = reference_date.year - event_date.year
            try:
                next_date = event_date.replace(year=event_date.year + years_diff)
            except ValueError:  # 2月29日
                next_date = event_date.replace(year=event_date.year + years_diff, day=28)
            if next_date < reference_date:
                next_date = self._add_delta(next_date, delta, event_date.day)
        else:
            while next_date < reference_date:
                next_date = self._add_delta(next_date, delta, event_date.day)

        return next_date

    # ============ 农历计算 (lunar_python) ============

    def _next_lunar_anniversary(
        self,
        event_date: date,  # 农历日期，用date类型存储
        repeat_type: "RepeatType",
        reference_date: date,
        is_leap=False,
    ) -> date | None:
        """计算农历纪念日的下一个公历日期"""
        lunar_month = event_date.month
        lunar_day = event_date.day

        if repeat_type == RepeatType.YEARLY:
            return self._next_lunar_yearly(lunar_month, lunar_day, reference_date, is_leap)
        elif repeat_type == RepeatType.MONTHLY:
            return self._next_lunar_monthly(lunar_day, reference_date, is_leap)
        elif repeat_type == RepeatType.DAILY:
            return reference_date  # 每天就是当天
        elif repeat_type == RepeatType.WEEKLY:
            # 周重复按公历处理
            solar_event = self._lunar_to_solar(event_date.year, lunar_month, lunar_day, is_leap)
            if solar_event:
                return self._next_gregorian_anniversary(solar_event, repeat_type, reference_date)
        else:
            # 半年/季度按农历月份处理
            return self._next_lunar_interval(event_date, repeat_type, reference_date, is_leap)

        return None

    def _next_lunar_yearly(
        self, lunar_month: int, lunar_day: int, reference_date: date, is_leap: bool
    ) -> date | None:
        """每年农历同一天"""
        # 获取参考日期对应的农历年
        ref_lunar = self._solar_to_lunar(reference_date)
        if not ref_lunar:
            return None

        start_year = ref_lunar.getYear()

        for year in range(start_year, start_year + 10):
            solar_date = self._lunar_to_solar(year, lunar_month, lunar_day, is_leap)
            if solar_date and solar_date >= reference_date:
                return solar_date

        return None

    def _next_lunar_monthly(
        self, lunar_day: int, reference_date: date, is_leap: bool
    ) -> date | None:
        """每月农历同一天"""
        ref_lunar = self._solar_to_lunar(reference_date)
        if not ref_lunar:
            return None

        year = ref_lunar.getYear()
        month = ref_lunar.getMonth()

        for _ in range(24):  # 最多查2年
            solar_date = self._lunar_to_solar(year, month, lunar_day, is_leap)
            if solar_date and solar_date >= reference_date:
                return solar_date

            # 下一个月
            month += 1
            if month > 12:
                month = 1
                year += 1

        return None

    def _next_lunar_interval(
        self, event_date: date, repeat_type: "RepeatType", reference_date: date, is_leap: bool
    ) -> date | None:
        """处理半年/季度等间隔的农历重复"""
        interval_months = {
            RepeatType.HALF_YEARLY: 6,
            RepeatType.THREE_MONTHLY: 3,
        }.get(repeat_type, 12)

        lunar_year = event_date.year
        lunar_month = event_date.month
        lunar_day = event_date.day

        for _ in range(50):  # 最多查50个周期
            solar_date = self._lunar_to_solar(lunar_year, lunar_month, lunar_day, is_leap)
            if solar_date and solar_date >= reference_date:
                return solar_date

            # 增加间隔月数
            lunar_month += interval_months
            while lunar_month > 12:
                lunar_month -= 12
                lunar_year += 1

        return None

    # ============ lunar_python 工具方法 ============

    def _lunar_to_solar(self, year: int, month: int, day: int, is_leap=False) -> date | None:
        """农历转公历"""
        month = not is_leap and month or -month
        try:
            lunar = Lunar.fromYmd(year, month, day)
            solar = lunar.getSolar()
            return date(solar.getYear(), solar.getMonth(), solar.getDay())
        except Exception:
            return None

    def _solar_to_lunar(self, d: date) -> Lunar | None:
        """公历转农历"""
        try:
            solar = Solar.fromYmd(d.year, d.month, d.day)
            return solar.getLunar()
        except Exception:
            return None

    # ============ 通用工具 ============

    def _get_repeat_delta(self, repeat_type: "RepeatType") -> relativedelta:
        """获取重复间隔"""
        return {
            RepeatType.YEARLY: relativedelta(years=1),
            RepeatType.HALF_YEARLY: relativedelta(months=6),
            RepeatType.THREE_MONTHLY: relativedelta(months=3),
            RepeatType.MONTHLY: relativedelta(months=1),
            RepeatType.WEEKLY: relativedelta(weeks=1),
            RepeatType.DAILY: relativedelta(days=1),
        }.get(repeat_type, relativedelta(years=1))

    def _add_delta(self, dt: date, delta: relativedelta, original_day: int) -> date:
        """添加间隔，处理月末日期"""
        result = dt + delta
        if result.day != original_day:
            try:
                result = result.replace(day=original_day)
            except ValueError:
                pass
        return result
