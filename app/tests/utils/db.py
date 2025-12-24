from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio.session import AsyncSession

from app.database.db import create_async_engine_and_session
from app.config import settings


TEST_DB_URL = settings.DB_MAIN_TEST_URL
_, async_test_db_session = create_async_engine_and_session(TEST_DB_URL)


async def override_get_session() -> AsyncGenerator[AsyncSession, None]:
    """session 生成器"""
    async with async_test_db_session() as session:
        yield session