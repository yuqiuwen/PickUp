import re
from datetime import date
from typing import Literal, Tuple, Annotated
from typing_extensions import Self

from pydantic import (
    BaseModel,
    Field,
    model_validator,
    ConfigDict,
    field_validator,
    EmailStr,
    field_serializer,
    SerializationInfo,
)

from app.constant import AuthType
from app.ext.crypt import pwd_crypto
from app.core.exception import ValidateError
from app.schemas.common import EntityModel

from app.utils.common import check_phone, hide_phone


def validate_user_pwd(pwd: str) -> Tuple[bool, str]:
    if len(pwd) > 20 or len(pwd) < 8:
        return False, "密码长度必须在8-20个字符"
    # if not re.match(r"^(?=.*[A-Z])(?=.*[a-z])(?=.*[0-9])[A-Za-z0-9@#!$%^&*]*$", pwd):
    #     return False, "密码必须至少同时包含大小写字母和数字"
    return True, ""


class SignSchema(BaseModel):
    account: str = Field()
    pwd: str = Field()

    @field_validator("account")
    @classmethod
    def validate_account(cls, v):
        # 验证账户
        if len(v) > 12 or len(v) < 6:
            raise ValidateError(errmsg="账号长度必须在6-12个字符")
        if not re.match(r"^[_a-zA-Z0-9-]+$", v):
            raise ValidateError(errmsg="账号只能包含英文、数字、下划线、短横线")

        return v

    @model_validator(mode="after")
    def validate_data(self) -> Self:
        self.pwd = pwd_crypto.decrypt(self.pwd, as_str=True)
        is_valid, errmsg = validate_user_pwd(self.pwd)
        if not is_valid:
            raise ValidateError(errmsg=errmsg)
        return self


class EmailSignSchema(BaseModel):
    """邮箱注册 Schema"""
    email: EmailStr = Field(description="邮箱地址")
    pwd: str = Field(description="密码（加密后）")
    code: str = Field(description="邮箱验证码")
    
    @field_validator("email")
    @classmethod
    def validate_email(cls, v):
        # 验证邮箱格式（EmailStr 已经验证了基本格式）
        if not v:
            raise ValidateError(errmsg="邮箱不能为空")
        return v.lower()  # 转为小写统一处理
    
    @model_validator(mode="after")
    def validate_data(self) -> Self:
        # 解密密码
        self.pwd = pwd_crypto.decrypt(self.pwd, as_str=True)
        is_valid, errmsg = validate_user_pwd(self.pwd)
        if not is_valid:
            raise ValidateError(errmsg=errmsg)
        
        # 验证码长度检查
        if not self.code or len(self.code) != 6:
            raise ValidateError(errmsg="验证码格式错误")
        
        return self


class SendEmailCodeSchema(BaseModel):
    """发送邮箱验证码 Schema"""
    email: EmailStr = Field(description="邮箱地址")
    biz: str = Field(description="业务场景: sign-注册, login-登录, set_pwd-重置密码")
    
    @field_validator("email")
    @classmethod
    def validate_email(cls, v):
        if not v:
            raise ValidateError(errmsg="邮箱不能为空")
        return v.lower()


class LoginSchema(BaseModel):
    auth_type: AuthType
    code_type: Literal["pwd", "code"]  # 凭证类型：验证码或密码
    code: str  # 凭证
    account: str  # 账号或手机号

    @model_validator(mode="after")
    def validate_data(self) -> Self:
        if self.code_type == "pwd":
            decrypted_code = pwd_crypto.decrypt(self.code, as_str=True)
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

    @model_validator(mode="after")
    def load_data(self):
        if self.validate_way not in ["pwd", "code"]:
            raise ValidateError("validate_way must be in [pwd, code]", errmsg="验证方式错误")

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
