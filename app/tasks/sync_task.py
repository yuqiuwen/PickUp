from celery.utils.log import get_task_logger

from app.database import db
from app.services.sync_data import SyncDataService
from app.tasks._runtime import run_coro
from make_celery import celery_app


logger = get_task_logger("job_log")


async def _sync_anniv_count():
    async with db.async_db_session() as session:
        return await SyncDataService.synchronize_anniv_count(session)


@celery_app.task()
def sync_anniv_count():
    return run_coro(_sync_anniv_count())
