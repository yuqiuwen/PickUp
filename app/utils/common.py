from collections import OrderedDict
import hashlib
import re
import secrets
from typing import Sequence
from email_validator import validate_email, EmailNotValidError

from app.constant import AuthType


def hide_phone(phone: str | None) -> str:
    """手机号脱敏"""
    return phone[:3] + "****" + phone[7:]


def check_phone(phone: str) -> bool:
    """校验国内手机号"""
    if len(phone) > 15 or not re.match(r"^1[3-9]\d{9}$", phone):
        return False
    return True


def is_email(email: str) -> bool:
    try:
        validate_email(email)
        return True
    except EmailNotValidError:
        return False


def is_phone(s: str, *, min_digits: int = 7, max_digits: int = 15) -> bool:
    PHONE_CLEAN_RE = re.compile(r"[\s\-\(\)\.]+")
    PHONE_RE = re.compile(r"^\+?\d+$")
    s = s.strip()
    if not s:
        return False

    cleaned = PHONE_CLEAN_RE.sub("", s)
    if not PHONE_RE.match(cleaned):
        return False

    digits = cleaned[1:] if cleaned.startswith("+") else cleaned
    return min_digits <= len(digits) <= max_digits


def is_account(s: str) -> bool:
    # 账号只能包含英文、数字、下划线、短横线
    ACCOUNT_RE = re.compile(r"^[A-Za-z0-9_-]+$")
    s = s.strip()
    return bool(ACCOUNT_RE.match(s))


def auto_detect_auth_type(raw: str) -> AuthType | None:
    s = raw.strip()
    if not s:
        return

    match s:
        case _ if is_email(s):
            return AuthType.EMAIL
        case _ if is_phone(s):
            return AuthType.PHONE
        case _ if is_account(s):
            return AuthType.ACCOUNT
        case _:
            return


def parse_sort_str(val: str) -> OrderedDict:
    """解析查询字符串中的排序条件

    Args:
        val (str): 多个排序字段以&分隔，模板：{field}.asc或desc，如id.desc&ctime.asc

    Returns:
        OrderedDict:
    """

    sort_dic = OrderedDict()
    for o in val.split("&"):
        field, sort = o.split(".")
        sort_dic[field] = sort
    return sort_dic


def diff_sequence_data(
    new: Sequence, old: Sequence, intersection=False
) -> tuple[set, set, set] | tuple[set, set]:
    """比较两个序列的变化：新增、删除、交集

    Args:
        new (Sequence): 新序列
        old (Sequence): 旧序列
        intersection (bool, optional): 是否返回交集. Defaults to False.

    Returns:
        tuple[set, set, set]: 新增，删除，交集
    """

    new, old = set(new), set(old)
    to_add = new - old
    to_del = old - new
    if not intersection:
        return to_add, to_del

    intersection = new & old
    return to_add, to_del, intersection


def gen_urlsafe_token(length=32) -> str:
    return secrets.token_urlsafe(length)


def hash_token(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()
