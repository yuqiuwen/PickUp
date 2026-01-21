from datetime import datetime, timezone
import time
from sqlalchemy import (
    Integer,
    MetaData,
    SmallInteger,
    String,
    BigInteger,
    TIMESTAMP,
    DateTime,
    Identity,
    func,
    text,
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.schema import Column
from ulid import ULID


convention = {
    "ix": "ix_%(table_name)s_%(column_0_N_label)s",  # Index
    "uq": "uq_%(table_name)s_%(column_0_N_name)s",  # Unique Constraint
    "ck": "ck_%(table_name)s_%(constraint_name)s",  # Check Constraint
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",  # Foreign
    "pk": "pk_%(table_name)s",  # primary key
}

metadata = MetaData(naming_convention=convention)
Base = declarative_base(metadata=metadata)


class BaseModel(Base):
    __abstract__ = True

    id = Column(Integer, Identity(), primary_key=True)


class ULIDModel(Base):
    __abstract__ = True

    id = Column(String(32), nullable=False, default=lambda: ULID().__str__(), primary_key=True)


class BaseBigModel(BaseModel):
    __abstract__ = True

    id = Column(BigInteger, Identity(), primary_key=True)


class TSModel(Base):
    __abstract__ = True

    ctime = Column(Integer, nullable=False, server_default=text("EXTRACT(EPOCH FROM now())::int"))
    utime = Column(
        Integer,
        nullable=False,
        onupdate=lambda: int(time.time()),
        server_default=text("EXTRACT(EPOCH FROM now())::int"),
    )


class TimeModel(Base):
    __abstract__ = True

    ctime = Column(TIMESTAMP, nullable=False, server_default=func.now())
    utime = Column(
        TIMESTAMP,
        nullable=False,
        onupdate=lambda: datetime.now(timezone.utc),
        server_default=func.now(),
    )


class OperatorModel(Base):
    __abstract__ = True

    create_by = Column(Integer, nullable=False, comment="创建人")
    update_by = Column(Integer, nullable=False, comment="更新人")


class BigOperatorModel(Base):
    __abstract__ = True

    create_by = Column(BigInteger, nullable=False, comment="创建人")
    update_by = Column(BigInteger, nullable=False, comment="更新人")


class StateModel(Base):
    __abstract__ = True

    state = Column(SmallInteger, nullable=False, default=1, comment="状态 1启用 0禁用 -1删除")
