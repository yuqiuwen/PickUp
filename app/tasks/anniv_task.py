from celery import shared_task
from celery.utils.log import get_task_logger
from app.constant import InviteTargetType
from app.database.db import async_db_session
from app.services.invite import InviteService
from make_celery import celery_app


logger = get_task_logger("job_log")


@celery_app.task(bind=True, queue="email-job")
async def send_email_invite(self, ttype: InviteTargetType, tid: str):
    async with async_db_session() as session:
        await InviteService(ttype).process_send_invite(session, tid)
    return
