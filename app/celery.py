from celery import Celery

from app.config import settings
from app.tasks.beat_schedules import BEAT_SCHEDULES




def init_celery_app() -> Celery:
    settings.CELERYBEAT_SCHEDULE_FILENAME.parent.mkdir(parents=True, exist_ok=True)
    celery = Celery(settings.APP_NAME)
    celery.conf.update(
        broker_url=settings.CELERY_BROKER_URL,
        result_backend=settings.CELERY_RESULT_BACKEND,
        beat_schedule_filename=str(settings.CELERYBEAT_SCHEDULE_FILENAME),
        timezone=settings.CELERY_TIMEZONE,
        enable_utc=settings.CELERY_ENABLE_UTC,
        task_track_started=settings.CELERY_TASK_TRACK_STARTED,
        task_acks_late=settings.CELERY_TASK_ACKS_LATE,
        task_always_eager=settings.CELERY_TASK_ALWAYS_EAGER,
        task_reject_on_worker_lost=settings.CELERY_TASK_REJECT_ON_WORKER_LOST,
        worker_send_task_events=settings.CELERY_WORKER_SEND_TASK_EVENTS,
        beat_schedule=BEAT_SCHEDULES,
        database_engine_options={
            "echo": settings.SQLALCHEMY_ECHO,
        },
    )


    celery.autodiscover_tasks(["app.tasks"])

    return celery


celery_app: Celery = init_celery_app()