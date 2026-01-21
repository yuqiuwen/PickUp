from enum import Enum

from app.core.app_code import AppCode


class APIException(Exception):
    def __init__(self, description=None, code=500, errmsg=None):
        super().__init__(description)
        self.description = description
        self.code = code
        self.errmsg = errmsg
        self.message = description


class AuthException(Exception):
    def __init__(self, message="auth exception", *, code: Enum = AppCode.AUTH_ERROR, errmsg=None):
        super().__init__(message)
        self.code: int = code.value
        if errmsg is None:
            errmsg = "认证异常"
        self.errmsg = errmsg
        self.message = message


class PermissionDenied(Exception):
    def __init__(self, message="", code: Enum = AppCode.FORBIDDEN, errmsg=None):
        super().__init__(message)
        if errmsg is None:
            errmsg = "权限不足，无法访问"
        if message == "":
            message = "permission denied"

        self.code = code.value
        self.errmsg = errmsg

        self.message = message


class ValidateError(Exception):
    def __init__(self, message="", code=422, errmsg="参数错误"):
        super().__init__(message)
        self.errmsg = errmsg
        self.code = code
        self.message = message


class DecryptedError(Exception):
    def __init__(self, message="", code=AppCode.DECRYPT_ERROR, errmsg=""):
        super().__init__(message)
        self.errmsg = errmsg
        self.code = code
        self.message = message


class ResourceLockedExc(Exception):
    def __init__(self, message="", code=AppCode.RESOURCE_LOCKED, errmsg=""):
        super().__init__(message)
        self.errmsg = errmsg
        self.code = code


class EmailHandleExc(Exception):
    def __init__(self, message="", code=AppCode.EMAIL_HANDLE_ERROR, errmsg=""):
        super().__init__(message)
        if errmsg is None:
            errmsg = "操作失败"
        if message == "":
            message = "operation failed"
        self.errmsg = errmsg
        self.code = code
        self.message = message


class EmailSendExc(Exception):
    def __init__(self, message="", code=AppCode.EMAIL_SEND_FAILED, errmsg=""):
        super().__init__(message)
        if errmsg is None:
            errmsg = "邮件发送失败"
        if message == "":
            message = "email send failed"
        self.errmsg = errmsg
        self.code = code
        self.message = message


class UserNotFoundError(Exception):
    def __init__(self, message="", code=AppCode.USER_NOT_FOUND, errmsg=""):
        super().__init__(message)
        if errmsg is None:
            errmsg = "用户不存在"
        if message == "":
            message = "user not found"
        self.errmsg = errmsg
        self.code = code
        self.message = message
