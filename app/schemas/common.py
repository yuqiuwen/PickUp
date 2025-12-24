from typing import Annotated, Any

from pydantic import BaseModel, Field, ConfigDict, TypeAdapter, BeforeValidator, field_validator

from app.constant import SMSSendBiz
from app.core.exception import ValidateError
from app.utils.common import check_phone


class PageModel(BaseModel):
    page: int = Field(1, ge=1)
    limit: int = Field(20, gt=0, le=200)


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
    def to_dantic_model(
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


class SmsSchema(BaseModel):
    biz: SMSSendBiz
    phone: str

    @field_validator("phone", mode="before")
    @classmethod
    def ensure_list(cls, value):
        if not check_phone(value):
            raise ValidateError(errmsg="手机号格式错误")
        return value
