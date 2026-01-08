from app.models.module import *


class SettingsModel(ULIDModel, TSModel, BigOperatorModel, StateModel):
    """系统设置"""

    __tablename__ = "settings"

    name = Column(String(50), nullable=False, comment="设置名称")
    value = Column(String(255), nullable=False, comment="设置值")
    description = Column(String(100), comment="描述")
    group = Column(String(20), nullable=False, comment="设置分组 SettingsGroup")
    type = Column(SmallInteger, nullable=False, comment="设置类型 SettingsType")
