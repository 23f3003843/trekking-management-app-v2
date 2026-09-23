web: gunicorn wsgi:app
worker: celery -A celery_worker.celery_app worker --loglevel=info
beat: celery -A celery_worker.celery_app beat --loglevel=info
