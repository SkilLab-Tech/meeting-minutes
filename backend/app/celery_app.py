from celery import Celery
import os

eager = os.getenv('CELERY_TASK_ALWAYS_EAGER', 'false').lower() == 'true'

celery_app = Celery(
    'meeting_minutes_tasks',
    broker=os.getenv('CELERY_BROKER_URL', 'redis://localhost:6379/0'),
    backend=os.getenv('CELERY_RESULT_BACKEND', 'redis://localhost:6379/0'),
)

celery_app.conf.update(
    task_always_eager=eager,
    task_store_eager_result=eager,
)

if eager:
    celery_app.conf.broker_url = 'memory://'
    celery_app.conf.result_backend = 'cache+memory://'
