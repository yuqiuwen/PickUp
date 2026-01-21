from datetime import datetime as dt, timedelta, timezone
from typing import Literal, ClassVar, Union, Optional

from dateutil.relativedelta import relativedelta
from zoneinfo import ZoneInfo


class DT:
    """
    统一的时间工具类，支持配置“应用/数据库时区”。

    默认使用 UTC，建议在应用启动时调用 DT.set_tz("Asia/Shanghai")
    或 DT.set_tz(settings.DB_TIMEZONE) 与数据库时区保持一致。
    """

    # 全局时区配置，默认 UTC
    _tz: ClassVar[ZoneInfo] = ZoneInfo("UTC")

    @classmethod
    def set_tz(cls, tz: Union[str, ZoneInfo]) -> None:
        """
        设置当前使用的时区，建议在应用启动时调用一次。

        e.g.
            DT.set_tz("Asia/Shanghai")
            DT.set_tz(ZoneInfo("Asia/Shanghai"))
        """
        if isinstance(tz, str):
            cls._tz = ZoneInfo(tz)
        else:
            cls._tz = tz

    @classmethod
    def tz(cls) -> ZoneInfo:
        """当前使用的时区（给外部查看用）"""
        return cls._tz

    # -------- 基础 now/ts/datetime 转换 --------

    @classmethod
    def now_time(cls) -> dt:
        """当前时间（带时区信息的 aware datetime）"""
        return dt.now(cls._tz)

    @classmethod
    def now_ts(cls) -> int:
        """当前时间对应的 Unix 时间戳（秒）"""
        # aware datetime.timestamp() 返回的是相对于 UTC 的秒数
        return int(cls.now_time().timestamp())

    @classmethod
    def now_year(cls) -> int:
        """当前时间对应的 Unix 时间戳（秒）"""
        # aware datetime.timestamp() 返回的是相对于 UTC 的秒数
        return cls.now_time().year

    @classmethod
    def ts2time(cls, timestamp: Union[int, float]) -> dt:
        """时间戳 -> datetime（使用当前配置的时区显示）"""
        return dt.fromtimestamp(timestamp, tz=cls._tz)

    @classmethod
    def time2ts(cls, time: dt) -> int:
        """
        datetime -> 时间戳（秒）

        - 如果传入是 naive datetime，按当前配置的时区解释；
        - 如果传入是 aware datetime，会先转到当前配置的时区再取 timestamp。
        """
        if time.tzinfo is None:
            time = time.replace(tzinfo=cls._tz)
        else:
            time = time.astimezone(cls._tz)
        return int(time.timestamp())

    # -------- 字符串 ↔ 时间 / 时间戳 --------

    @classmethod
    def now_str(cls, format_str: str = "%Y-%m-%d %H:%M:%S") -> str:
        return cls.now_time().strftime(format_str)

    @classmethod
    def str2time(
        cls,
        s: str,
        format_str: str = "%Y-%m-%d %H:%M:%S",
    ) -> dt:
        """
        字符串 -> datetime（按当前时区解释）

        例如数据库/前端给的 "2024-01-01 10:00:00"，认为是“当前时区”的 10:00。
        """
        naive = dt.strptime(s, format_str)
        return naive.replace(tzinfo=cls._tz)

    @classmethod
    def str2ts(
        cls,
        s: str,
        format_str: str = "%Y-%m-%d %H:%M:%S",
        precision: Literal["s", "ms", "us"] = "s",
    ) -> int:
        """将时间字符串转换为时间戳"""
        t = cls.str2time(s, format_str)  # 已经是当前时区的 aware datetime
        base = t.timestamp()
        if precision == "s":
            return int(base)
        elif precision == "ms":
            return int(base * 1000)
        elif precision == "us":
            return int(base * 1_000_000)
        # 理论上 precision 已经被 Literal 限定，不会走到这一步
        raise ValueError(f"unsupported precision: {precision}")

    @classmethod
    def str2date(cls, s: str, format_str: str = "%Y-%m-%d") -> dt.date:
        """字符串 -> date（与时区无关，仅日期）"""
        return dt.strptime(s, format_str).date()

    @classmethod
    def date2str(cls, d: dt.date, format_str: str = "%Y-%m-%d") -> str:
        """date -> 字符串"""
        return d.strftime(format_str)

    @classmethod
    def ts2str(cls, t: Union[int, float], format_str: str = "%Y-%m-%d %H:%M:%S") -> str:
        """时间戳 -> 字符串（按当前时区显示）"""
        return cls.ts2time(t).strftime(format_str)

    @classmethod
    def fmt_time(cls, d: dt, format_str: str = "%Y-%m-%d %H:%M:%S") -> str:
        """datetime -> 字符串（保持其自身时区，不强制转换）"""
        return d.strftime(format_str)

    # -------- 日期 / 起止时间 --------

    @classmethod
    def today(cls) -> dt.date:
        """当前时区下的“今天”的日期"""
        return cls.now_time().date()

    @classmethod
    def start_of_date(cls, d: dt.date) -> dt:
        """某天 00:00:00（当前时区）"""
        # Python 3.11+ 支持 tzinfo 参数；为兼容可用 replace
        return dt.combine(d, dt.min.time()).replace(tzinfo=cls._tz)

    @classmethod
    def end_of_date(cls, d: dt.date) -> dt:
        """某天 23:59:59.999999（当前时区）"""
        return dt.combine(d, dt.max.time()).replace(tzinfo=cls._tz)

    # -------- 相对时间计算（天/周/月/年） --------

    @classmethod
    def n_day_ago(cls, days: int, to: Optional[dt] = None) -> dt:
        """n 天前的时间（相对于 to，默认当前时区 now）"""
        if to is None:
            to = cls.now_time()
        return to - timedelta(days=days)

    @classmethod
    def after_n_day(cls, days: int, to: Optional[dt] = None) -> dt:
        """n 天后的时间"""
        if to is None:
            to = cls.now_time()
        return to + timedelta(days=days)

    @classmethod
    def n_year_ago(cls, years: int, end: Optional[dt] = None) -> dt:
        if end is None:
            end = cls.now_time()
        return end - relativedelta(years=years)

    @classmethod
    def after_n_year(cls, years: int, start: Optional[dt] = None) -> dt:
        if start is None:
            start = cls.now_time()
        return start + relativedelta(years=years)

    @classmethod
    def n_month_ago(cls, months: int, end: Optional[dt] = None) -> dt:
        if end is None:
            end = cls.now_time()
        return end - relativedelta(months=months)

    @classmethod
    def after_n_month(cls, months: int, start: Optional[dt] = None) -> dt:
        if start is None:
            start = cls.now_time()
        return start + relativedelta(months=months)

    @classmethod
    def n_week_ago(cls, weeks: int, end: Optional[dt] = None) -> dt:
        if end is None:
            end = cls.now_time()
        return end - timedelta(weeks=weeks)

    @classmethod
    def after_n_week(cls, weeks: int, start: Optional[dt] = None) -> dt:
        if start is None:
            start = cls.now_time()
        return start + timedelta(weeks=weeks)
