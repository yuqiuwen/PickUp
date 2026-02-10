"""
周期任务
example:
    "task_name": {
        "task": "app.tasks.task_name",
        "schedule": "*/1 * * * *",
        "args": ()
    }

"""

from celery.schedules import crontab


BEAT_SCHEDULES = {
    "sync_anniv_count": {
        "task": "app.tasks.sync_task.sync_anniv_count",
        "schedule": crontab(minute="08", hour="*/6"),
        "args": (),
    },
}
