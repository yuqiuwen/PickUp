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


class PermitExceededException(Exception):
    def __init__(self, message="", code: Enum = AppCode.FORBIDDEN, errmsg=None):
        super().__init__(message)
        self.code = code.value
        if errmsg is None:
            errmsg = "权限不足，无法访问"
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
