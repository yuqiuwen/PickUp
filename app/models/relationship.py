from app.constant import FollowState
from app.models.module import *


class UserFollow(BaseBigModel, TSModel):
    """关注"""

    __tablename__ = "user_follow"
    __table_args__ = (UniqueConstraint("from_uid", "to_uid", name="uq_follow_from_to"),)

    from_uid = Column(BigInteger, nullable=False, comment="关注者id")
    to_uid = Column(BigInteger, nullable=False, comment="关注对象id")
    state = Column(SmallInteger, nullable=False, default=FollowState.FOLLOWING, comment="关注状态")


class UserFan(BaseBigModel, TSModel):
    """粉丝"""

    __tablename__ = "user_fan"
    __table_args__ = (UniqueConstraint("from_uid", "to_uid", name="uq_fan_from_to"),)

    from_uid = Column(BigInteger, nullable=False, comment="关注者id")
    to_uid = Column(BigInteger, nullable=False, comment="关注对象id")
    state = Column(SmallInteger, nullable=False, default=FollowState.FOLLOWING, comment="关注状态")
