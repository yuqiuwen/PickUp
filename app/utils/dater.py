from datetime import datetime as dt, timedelta
from typing import Literal

from dateutil.relativedelta import relativedelta


class DT:
    @classmethod
    def now_ts(cls):
        return int(dt.now().timestamp())

    @classmethod
    def now_time(cls):
        return dt.now()

    @classmethod
    def ts2time(cls, timestamp):
        return dt.fromtimestamp(timestamp)

    @classmethod
    def time2ts(cls, time) -> int:
        return int(time.timestamp())

    @classmethod
    def now_str(cls, format_str: str = "%Y-%m-%d %H:%M:%S") -> str:
        return dt.now().strftime(format_str)

    @classmethod
    def today(cls):
        return cls.now_time().date()

    @classmethod
    def str2time(cls, s: str, format_str: str = "%Y-%m-%d %H:%M:%S") -> dt:
        return dt.strptime(s, format_str)

    @classmethod
    def str2ts(
        cls,
        s: str,
        format_str: str = "%Y-%m-%d %H:%M:%S",
        precision: Literal["s", "ms", "us"] = "s",
    ) -> int:
        """将时间字符串转换为时间戳"""
        t = cls.str2time(s, format_str)
        if precision == "s":
            return int(t.timestamp())
        elif precision == "ms":
            return int(t.timestamp() * 1000)
        elif precision == "us":
            return int(t.timestamp() * 1000000)

    @classmethod
    def str2date(cls, s: str, format_str: str = "%Y-%m-%d") -> dt.date:
        return dt.strptime(s, format_str).date()

    @classmethod
    def date2str(cls, d: dt.date, format_str: str = "%Y-%m-%d") -> dt.date:
        return d.strftime(format_str)

    @classmethod
    def ts2str(cls, t, format_str: str = "%Y-%m-%d %H:%M:%S") -> str:
        return dt.fromtimestamp(t).strftime(format_str)

    @classmethod
    def start_of_date(cls, d: dt.date):
        return dt.combine(d, dt.min.time())

    @classmethod
    def end_of_date(cls, d: dt.date):
        return dt.combine(d, dt.max.time())

    @classmethod
    def fmt_time(cls, d: dt, format_str: str = "%Y-%m-%d %H:%M:%S") -> str:
        return d.strftime(format_str)

    @classmethod
    def n_day_ago(cls, days: int, to=None) -> dt:
        """n天前的时间"""
        if not to:
            to = cls.now_time()

        return to - timedelta(days=days)

    @classmethod
    def after_n_day(cls, days: int, to=None) -> dt:
        """n天后的时间"""
        if not to:
            to = cls.now_time()

        return to + timedelta(days=days)

    @classmethod
    def n_year_ago(cls, years: int, end=None):
        if not end:
            end = cls.now_time()

        return end - relativedelta(years=years)

    @classmethod
    def after_n_year(cls, years: int, start=None):
        if not start:
            start = cls.now_time()

        return start + relativedelta(years=years)

    @classmethod
    def n_month_ago(cls, months: int, end=None):
        if not end:
            end = cls.now_time()

        return end - relativedelta(months=months)

    @classmethod
    def after_n_month(cls, months: int, start=None):
        if not start:
            start = cls.now_time()

        return start + relativedelta(months=months)

    @classmethod
    def n_week_ago(cls, weeks: int, end=None):
        if not end:
            end = cls.now_time()

        return end - timedelta(weeks=weeks)

    @classmethod
    def after_n_week(cls, weeks: int, start=None):
        if not start:
            start = cls.now_time()

        return start + timedelta(weeks=weeks)
