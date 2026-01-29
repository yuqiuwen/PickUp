import asyncio
from celery import shared_task
from celery.utils.log import get_task_logger
from app.constant import InviteTargetType
import app.database.db as db
from app.services.invite import InviteService
from app.tasks._runtime import run_coro
from make_celery import celery_app


logger = get_task_logger("job_log")


async def _send_email_invite(ttype: InviteTargetType, tid: str):
    async with db.async_db_session() as session:
        return await InviteService(ttype).process_send_invite(session, tid)


@celery_app.task(bind=True, queue="email-job")
def send_email_invite(self, ttype: InviteTargetType, tid: str):
    return run_coro(_send_email_invite(ttype, tid))
