from app.constant import CommentState
from app.models.module import *


class CommentModel(BaseBigModel):
    """评论"""

    __tablename__ = "comment"
    __table_args__ = (Index("ix_comment_rtype_rid_ctime", "rtype", "rid", "ctime"),)

    id = Column(BigInteger, primary_key=True)
    parent_id = Column(BigInteger, nullable=False, default=-1, index=True, comment="父评论id")
    root_id = Column(BigInteger, nullable=False, default=-1, comment="根评论id")
    rtype = Column(SmallInteger, nullable=False, comment="评论的资源类型")
    rid = Column(String(32), nullable=False, comment="评论的资源id")

    content = Column(Text, comment="评论内容")
    from_uid = Column(BigInteger, nullable=False, index=True, comment="评论者")
    to_uid = Column(BigInteger, nullable=False, index=True, comment="被评论者")
    like_cnt = Column(Integer, default=0, comment="点赞数")
    dlike_cnt = Column(Integer, default=0, comment="点踩数")
    reply_cnt = Column(Integer, default=0, comment="回复数")
    ip = Column(String(40), comment="ip地址")
    state = Column(
        SmallInteger, nullable=False, default=CommentState.ENABLED, comment="状态 CommentState"
    )
    score = Column(DECIMAL(14, 6), default=0, comment="热度值")
    is_top = Column(Boolean, nullable=False, default=False, comment="是否置顶")
    ctime = Column(Integer, nullable=False, server_default=text("EXTRACT(EPOCH FROM now())::int"))

    user = relationship(
        "User",
        lazy="joined",
        viewonly=True,
        uselist=False,
        primaryjoin="CommentModel.from_uid==foreign(User.id)",
    )
