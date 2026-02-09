from datetime import datetime
from typing import Annotated
import typing

from pydantic import BeforeValidator, Field, PlainSerializer

from app.utils.dater import DT


def serialize_timestamp_date_only(value: int) -> str:
    """时间戳转日期字符串"""
    return DT.ts2str(value, "%Y-%m-%d")


def TimestampField(format_str: str = "%Y-%m-%d %H:%M:%S"):
    """可传参的时间戳字段工厂函数"""

    def validate(value: str) -> int:
        if isinstance(value, int):
            return value
        return DT.str2ts(value, format_str)

    def serialize(value: int) -> str:
        """时间戳转字符串"""
        return DT.ts2str(value, format_str)

    return Annotated[
        int | None,
        BeforeValidator(validate),
        PlainSerializer(serialize, return_type=str | None),
        Field(description="时间戳字段，序列化为时间字符串"),
    ]


def AutoFormatTimeField(format_str: str = "%Y-%m-%d %H:%M:%S") -> type:
    """自动格式化时间"""

    def validate(value: str) -> datetime:
        if isinstance(value, datetime):
            return value
        return DT.str2time(value, format_str)

    def serialize(value: datetime) -> str:
        """时间戳转字符串"""
        return DT.fmt_time(value, format_str)

    return Annotated[
        datetime | None,
        BeforeValidator(validate),
        PlainSerializer(serialize, return_type=str | None),
        Field(description="时间字段，序列化为时间字符串"),
    ]


def DelimitedList(item_type: typing.Type, separator: str = ","):
    def parse(v: any):
        if isinstance(v, str):
            return [item_type(x.strip()) for x in v.split(separator)]
        return v

    return Annotated[typing.List[item_type], BeforeValidator(parse)]
