from app.constant import MediaState, MediaType, SettingsGroup, SettingsSwitch
from app.models.module import *


class SettingsModel(BaseModel, TSModel, BigOperatorModel, StateModel):
    """系统设置"""

    __tablename__ = "settings"

    name = Column(String(100), nullable=False, unique=True, comment="设置唯一名称")
    label = Column(String(50), nullable=False, comment="设置显示名称")
    value = Column(String(255), nullable=False, comment="设置值")
    description = Column(String(100), comment="描述")
    group = Column(String(20), nullable=False, comment="设置分组 SettingsGroup")


class MediaModel(ULIDModel, TSModel):
    """媒体文件"""

    __tablename__ = "media"

    type = Column(SmallInteger, nullable=False, comment="媒体类型: `MediaType`")
    path = Column(String, nullable=False, unique=True)
    state = Column(
        SmallInteger,
        nullable=False,
        default=MediaState.UNREVIEWED,
        index=True,
        comment="状态",
    )
