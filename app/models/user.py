import time

import bcrypt

from app.constant import UserType
from app.models.module import *


class User(BaseModel, TSModel):
    """用户表"""

    __tablename__ = "user"

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
