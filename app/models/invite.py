import secrets
from app.constant import InviteState
from app.models.module import *


class Invite(ULIDModel, TSModel):
    __tablename__ = "invite"

    ttype = Column(SmallInteger, nullable=False, comment="目标对象类型InviteTargetType")
    tid = Column(String, nullable=False, index=True, comment="目标对象ID")

    inviter_id = Column(BigInteger, nullable=False, index=True)
    invitee_email = Column(String(320), nullable=False, index=True)
    invitee_user_id = Column(BigInteger, nullable=True, index=True, comment="邀请用户ID")
    token = Column(
        String(64),
        nullable=False,
        unique=True,
        index=True,
        default=lambda: secrets.token_urlsafe(32),
        comment="邮件链接里携带",
    )
    state = Column(SmallInteger, nullable=False, default=InviteState.PENDING, comment="InviteState")
    expires_at = Column(DateTime(timezone=True), nullable=False)
    responded_at = Column(DateTime(timezone=True))
    message = Column(Text, comment="邀请邮件内容")
    meta = Column(
        JSONB, nullable=False, default=dict, comment="存元数据，如角色/权限/邀请来源等额外信息"
    )
