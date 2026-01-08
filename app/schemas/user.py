import re
from datetime import date
from typing import Literal, Tuple, Annotated
from typing_extensions import Self

from pydantic import (
    BaseModel,
    Field,
    ValidationInfo,
    model_validator,
    ConfigDict,
    field_validator,
    EmailStr,
    field_serializer,
    SerializationInfo,
    validate_email,
)

from app.constant import AuthType, SMSSendBiz
from app.ext.crypt import pwd_crypto
from app.core.exception import ValidateError
from app.schemas.common import EntityModel

from app.utils.common import auto_detect_auth_type, check_phone, hide_phone


def validate_user_pwd(pwd: str) -> Tuple[bool, str]:
    if len(pwd) > 20 or len(pwd) < 8:
        return False, "密码长度必须在8-20个字符"
    # if not re.match(r"^(?=.*[A-Z])(?=.*[a-z])(?=.*[0-9])[A-Za-z0-9@#!$%^&*]*$", pwd):
    #     return False, "密码必须至少同时包含大小写字母和数字"
    return True, ""


def validate_account(account: str) -> bool:
    if len(account) > 12 or len(account) < 6:
        raise ValidateError(errmsg="账号长度必须在6-12个字符")
    if not re.match(r"^[_a-zA-Z0-9-]+$", account):
        raise ValidateError(errmsg="账号只能包含英文、数字、下划线、短横线")
    return True


class SignSchema(BaseModel):
    """
    注册 Schema
    账号和邮箱登录需要密码，其他登录方式不需要密码
    """

    auth_type: AuthType
    account: str = Field(
        description="账号/手机号/邮箱/微信，其中账号只能包含英文、数字、下划线、短横线，长度必须在6-12个字符"
    )
    pwd: str = Field(default=None, description="密码（加密后）")
    code: str = Field(default=None, description="验证码")
    username: str = Field(default=None, description="用户名")
    is_encrypted: bool = Field(default=True, description="是否已加密")

    @model_validator(mode="after")
    def validate_data(self) -> Self:
        if self.username:
            if len(self.username) > 20 or len(self.username) < 4:
                raise ValidateError(errmsg="用户名长度必须在4-20个字符")

        if self.auth_type in (AuthType.ACCOUNT, AuthType.EMAIL):
            if not self.pwd:
                raise ValidateError(errmsg="密码不能为空")
            if self.auth_type == AuthType.ACCOUNT:
                validate_account(self.account)

            if self.is_encrypted:
                self.pwd = pwd_crypto.decrypt(self.pwd, as_str=True)
                is_valid, errmsg = validate_user_pwd(self.pwd)
                if not is_valid:
                    raise ValidateError(errmsg=errmsg)

        elif self.auth_type == AuthType.PHONE:
            if not check_phone(self.account):
                raise ValidateError(errmsg="手机号格式错误")

        elif self.auth_type == AuthType.EMAIL:
            if not validate_email(self.account):
                raise ValidateError(errmsg="邮箱格式错误")
        return self


class LoginSchema(BaseModel):
    auth_type: AuthType | None = Field(default=None, description="登录方式，不传则自动推测")
    code_type: Literal["pwd", "code"]  # 凭证类型：验证码或密码
    code: str  # 凭证
    account: str  # 账号或手机号

    @model_validator(mode="after")
    def validate_data(self, info: ValidationInfo) -> Self:
        if not self.auth_type:
            self.auth_type = auto_detect_auth_type(self.account)
        if self.code_type == "pwd":
            if (info.context or {}).get("is_encrypted", True):
                decrypted_code = pwd_crypto.decrypt(self.code, as_str=True)
            else:
                decrypted_code = self.code
            is_valid, errmsg = validate_user_pwd(decrypted_code)
            if not is_valid:
                raise ValidateError(errmsg=errmsg)
            self.code = decrypted_code

        if self.auth_type == AuthType.ACCOUNT:
            if self.code_type != "pwd":
                raise ValueError("参数错误")

        elif self.auth_type == AuthType.PHONE:
            if not check_phone(self.account):
                raise ValueError("手机号格式错误")

        return self


class UserSchema(EntityModel):
    id: int
    username: str
    account: str | None
    birth: date | None
    gender: int | None
    phone: str | None
    email: EmailStr | None
    title: str | None
    introduce: str | None
    ctime: int
    utime: int | None

    @field_serializer("phone")
    def serialize_phone(self, value: str, info: SerializationInfo) -> str:
        # 将datetime对象转换为特定格式的字符串
        context = info.context
        if context and context.get("mask_phone", False) and value:
            value = hide_phone(value)
        return value


class UserAuthInfoSchema(BaseModel):
    id: int
    auth_type: AuthType


class ModifyPwdSchema(BaseModel):
    cur_pwd: str | None = None
    new_pwd: str
    validate_way: Literal["pwd", "code"]  # 验证方式：验证码或密码
    code: str | None = None
    account: str | None = None
    auth_type: AuthType | None = None

    @model_validator(mode="after")
    def load_data(self):
        if self.account is not None:
            self.auth_type = auto_detect_auth_type(self.account)

        self.new_pwd = pwd_crypto.decrypt(self.new_pwd, as_str=True)
        if self.validate_way == "pwd":
            if not self.cur_pwd:
                raise ValidateError(errmsg="原密码不存在")

            self.cur_pwd = pwd_crypto.decrypt(self.cur_pwd, as_str=True)
            if self.cur_pwd == self.new_pwd:
                raise ValidateError(errmsg="原密码和新密码不能相同")

            is_valid, errmsg = validate_user_pwd(self.new_pwd)
            if not is_valid:
                raise ValidateError(errmsg=errmsg)
        else:
            if not self.code:
                raise ValidateError(errmsg="验证码不能为空")
            if not self.account:
                raise ValidateError(errmsg="邮箱或手机号不能为空")
        return self


class SetPwdSchema(BaseModel):
    code: str
    new_pwd: str

    @model_validator(mode="after")
    def load_data(self):
        pwd = pwd_crypto.decrypt(self.new_pwd, as_str=True)
        is_valid, errmsg = validate_user_pwd(pwd)
        if not is_valid:
            raise ValidateError(errmsg=errmsg)
        self.new_pwd = pwd
        return self


class UpdateUserSchema(BaseModel):
    username: str | None = Field(default=None, description="用户名", min_length=4, max_length=20)
    title: str | None = Field(default=None, description="头衔", max_length=20)
    introduce: str | None = Field(default=None, description="介绍", max_length=100)
    gender: int | None = Field(default=None, description="性别 0女 / 1男")
    birth: date | None = None
    avatar: str | None = None
