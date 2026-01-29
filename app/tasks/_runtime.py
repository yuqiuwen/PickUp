# celery_runtime.py
import asyncio
from celery.signals import worker_process_init, worker_process_shutdown
from app.database.db import init_async_engine_and_session, async_engine
from app.config import settings

_worker_loop: asyncio.AbstractEventLoop | None = None


@worker_process_init.connect
def on_worker_process_init(**kwargs):
    global _worker_loop
    _worker_loop = asyncio.new_event_loop()
    asyncio.set_event_loop(_worker_loop)

    # 在“子进程 + 已设置的 loop”环境里初始化 DB（关键）
    init_async_engine_and_session(settings.DB_MAIN_URL)


@worker_process_shutdown.connect
def on_worker_process_shutdown(**kwargs):
    global _worker_loop
    if _worker_loop and not _worker_loop.is_closed():
        # 优雅释放连接池
        if async_engine is not None:
            _worker_loop.run_until_complete(async_engine.dispose())
        _worker_loop.close()


def run_coro(coro):
    assert _worker_loop is not None
    return _worker_loop.run_until_complete(coro)
