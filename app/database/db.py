import sys
from typing import AsyncGenerator

from sqlalchemy import URL, create_engine
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    create_async_engine,
    AsyncSession,
    async_sessionmaker,
)
from sqlalchemy.orm import sessionmaker
from sqlmodel import Field, Session, SQLModel, select

from app.config import settings
from app.core.loggers import app_logger


def create_async_engine_and_session(
    url: str | URL,
) -> tuple[AsyncEngine, async_sessionmaker[AsyncSession]]:
    try:
        async_engine = create_async_engine(
            url,
            echo=settings.SQLALCHEMY_ECHO,
            future=True,
            pool_pre_ping=True,
            pool_size=10,
            max_overflow=20,
            pool_timeout=30,
            # sqlite加上此参数
            # connect_args={"check_same_thread": False},
        )

    except Exception as e:
        app_logger.critical(f"数据库连接失败 {e}")
        sys.exit()
    else:
        async_session = async_sessionmaker(
            bind=async_engine,
            class_=AsyncSession,
            expire_on_commit=False,
        )
        return async_engine, async_session


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    async with async_db_session() as session:
        yield session


async_engine, async_db_session = create_async_engine_and_session(settings.DB_MAIN_URL)
