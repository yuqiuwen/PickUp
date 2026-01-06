from datetime import datetime, timezone
import time
from sqlalchemy import Integer, String, BigInteger, TIMESTAMP, DateTime, Identity, func, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.schema import Column
from ulid import ULID


Base = declarative_base()


class BaseModel(Base):
    __abstract__ = True

    id = Column(Integer, primary_key=True)


class ULIDModel(Base):
    __abstract__ = True

    id = Column(String(32), nullable=False, default=lambda: ULID().__str__(), primary_key=True)


class BaseBigModel(BaseModel):
    __abstract__ = True

    id = Column(BigInteger, primary_key=True)


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
