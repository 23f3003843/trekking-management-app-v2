from celery.schedules import crontab
from app import create_app
from extensions import celery_app

flask_app = create_app()

#Configure Celery using the broker and result backend settings from Flask
celery_app.conf.update(
    broker_url=flask_app.config["CELERY_BROKER_URL"],
    result_backend=flask_app.config["CELERY_RESULT_BACKEND"],
    timezone="Asia/Kolkata",
    enable_utc=True,
)

import tasks

#Custom Celery Task class that provides Flask application context to tasks
class _ContextTask(celery_app.Task):
    def __call__(self, *args, **kwargs):
        with flask_app.app_context():
            return self.run(*args, **kwargs)

celery_app.Task = _ContextTask
#Celery Beat to run scheduled tasks automatically
celery_app.conf.beat_schedule = {
    #Send daily reminders for upcoming treks at 8:00 AM
    "daily-trek-reminders": {
        "task": "tasks.dailyTrek_reminders",
        "schedule": crontab(hour=8, minute=0),
    },
    #Generate the monthly activity report on the 1st of every month at 6:00 AM
    "monthly-activity-report": {
        "task": "tasks.monthly_report",
        "schedule": crontab(hour=6, minute=0, day_of_month=1),
    },
}

if __name__ == "__main__":
    celery_app.start()
