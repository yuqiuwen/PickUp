from typing import Annotated, Any

from pydantic import BaseModel, Field, ConfigDict, TypeAdapter, BeforeValidator, field_validator
from pydantic import EmailStr

from app.constant import MediaType, SMSSendBiz
from app.core.exception import ValidateError
from app.utils.common import check_phone, parse_sort_str


class PageQueryModel(BaseModel):
    page: int = Field(1, ge=1)
    limit: int = Field(20, gt=0, le=200)


class CursorPageQueryModel(BaseModel):
    last: Any = Field(0)
    limit: int = Field(20, gt=0, le=200)


class OrderByModel(BaseModel):
    order_by: str = Field(
        default=None, description="多个排序字段以&分隔，格式：field.asc/desc，如id.desc&ctime.asc"
    )

    @field_validator("order_by", mode="before")
    @classmethod
    def parse_order(cls, value: str) -> str:
        if not value:
            return
        return parse_sort_str(value)


class EntityModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    @classmethod
    def dump(
        cls,
        instance,
        include=None,
        exclude=None,
        context=None,
        by_alias: bool = False,
        exclude_unset: bool = False,
        exclude_defaults: bool = False,
        exclude_none: bool = False,
    ):
        return cls.model_validate(instance, from_attributes=True).model_dump(
            context=context,
            include=include,
            exclude=exclude,
            by_alias=by_alias,
            exclude_unset=exclude_unset,
            exclude_defaults=exclude_defaults,
            exclude_none=exclude_none,
        )

    @classmethod
    def dump_many(
        cls,
        instances,
        include=None,
        exclude=None,
        by_alias=None,
        exclude_unset=False,
        exclude_defaults=False,
        exclude_none=False,
    ):
        return TypeAdapter(list[cls]).dump_python(
            instances,
            include=include,
            exclude=exclude,
            by_alias=by_alias,
            exclude_unset=exclude_unset,
            exclude_defaults=exclude_defaults,
            exclude_none=exclude_none,
        )

    @classmethod
    def to_dantic_model_list(
        cls,
        instances,
        strict: bool | None = None,
        from_attributes: bool | None = True,
        context: dict[str, any] | None = None,
    ):
        """使用 pydantic 原生方法转换为字典列表"""
        return TypeAdapter(list[cls]).validate_python(
            instances, from_attributes=from_attributes, strict=strict, context=context
        )

    @classmethod
    def to_dantic_model(
        cls,
        instance,
        strict: bool | None = None,
        from_attributes: bool | None = True,
        context: dict[str, any] | None = None,
    ):
        """使用 pydantic 原生方法转换为字典列表"""
        return TypeAdapter(cls).validate_python(
            instance, from_attributes=from_attributes, strict=strict, context=context
        )


class SmsSchema(BaseModel):
    biz: SMSSendBiz
    phone: str

    @field_validator("phone", mode="before")
    @classmethod
    def ensure_list(cls, value):
        if not check_phone(value):
            raise ValidateError(errmsg="手机号格式错误")
        return value


class EmailSchema(BaseModel):
    biz: SMSSendBiz
    email: EmailStr


class UpdateMediaSchema(BaseModel):
    id: str | None = Field(default=None)
    type: MediaType
    path: str


class TagsSchema(EntityModel):
    id: str
    name: str


class MediaSchema(EntityModel):
    id: str | None = Field(default=None)
    type: MediaType
    path: str
