from app.models.module import *


class UserInteraction(ULIDModel, TSModel):
    """点赞、收藏记录"""

    __tablename__ = "user_interaction"
    __table_args__ = (
        UniqueConstraint(
            "action", "rtype", "rid", "uid", name="uq_user_interaction_action_rtype_rid_uid"
        ),
    )

    action = Column(SmallInteger, nullable=False, comment="行为，UserInterActionEnum")
    rid = Column(String(36), nullable=False, comment="资源id")
    rtype = Column(SmallInteger, nullable=False, comment="资源类型 ResourceType")
    uid = Column(BigInteger, nullable=False, comment="用户id")
    owner_uid = Column(BigInteger, comment="资源作者id")
    state = Column(SmallInteger, nullable=False, default=1, comment="状态：1收藏 0取消收藏")
