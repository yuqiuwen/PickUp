import re


def hide_phone(phone: str | None) -> str:
    """手机号脱敏"""
    return phone[:3] + "****" + phone[7:]


def check_phone(phone: str) -> bool:
    """校验国内手机号"""
    if len(phone) > 15 or not re.match(r"^1[3-9]\d{9}$", phone):
        return False
    return True
