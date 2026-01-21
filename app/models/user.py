import time

import bcrypt
from sqlalchemy import outerjoin

from app.constant import GroupRole, UserType
from app.models.module import *


class User(BaseModel, TSModel):
    """用户表"""

    __tablename__ = "user"

    id = Column(BigInteger, Identity(always=True, start=10000001), primary_key=True)
    account = Column(String(20), unique=True)
    username = Column(String(50), nullable=False)
    password_hash = Column(String(128))
    avatar = Column(String)
    gender = Column(SmallInteger, comment="性别 0女 / 1男")
    birth = Column(Date)
    phone = Column(String(15), unique=True)
    email = Column(String(50), unique=True)
    title = Column(String(20))
    introduce = Column(String(100))
    type = Column(SmallInteger, nullable=False, default=UserType.NORMAL)

    @property
    def password(self):
        raise AttributeError("can't read password!")

    @password.setter
    def password(self, value):
        salt = bcrypt.gensalt(rounds=12)
        self.password_hash = bcrypt.hashpw(value.encode("utf-8"), salt).decode()

    def password_valid(self, password):
        """验证密码是否正确"""
        if not self.password_hash:
            return False

        return bcrypt.checkpw(password.encode("utf-8"), self.password_hash.encode("utf8"))


class UserDevices(ULIDModel, TSModel):
    """用户设备"""

    __tablename__ = "user_device"

    user_id = Column(BigInteger, nullable=False, comment="用户ID")
    device_id = Column(String(32), nullable=False, comment="设备ID")
    device_type = Column(SmallInteger, nullable=False, comment="设备类型")
    device_token = Column(String(255), nullable=False, comment="设备Token")


class UserSettings(TSModel):
    """用户设置"""

    __tablename__ = "user_settings"

    user_id = Column(BigInteger, primary_key=True, comment="用户ID")
    settings_id = Column(Integer, primary_key=True, comment="设置ID SettingsModel.id")
    value = Column(String, comment="设置值, 默认为settings.value")


class ShareGroupModel(ULIDModel, TSModel, BigOperatorModel):
    """共享组"""

    __tablename__ = "share_group"

    owner_id = Column(BigInteger, nullable=False, index=True)
    name = Column(String(50), nullable=False, index=True, comment="共享组名称")
    description = Column(String(100), comment="描述")
    cover = Column(String(255), comment="封面")
    max_members = Column(Integer, nullable=False, default=100, comment="最大成员数")
    is_public = Column(SmallInteger, nullable=False, default=1, comment="0私密 1公开")


class ShareGroupMemberModel(TSModel):
    """共享组成员"""

    __tablename__ = "share_group_member"

    group_id = Column(String(32), primary_key=True)
    user_id = Column(BigInteger, primary_key=True)
    role = Column(SmallInteger, nullable=False, default=GroupRole.MEMBER, comment="GroupRole")
