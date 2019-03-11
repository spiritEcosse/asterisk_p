from __future__ import absolute_import
from celery import Celery
from django.conf import settings
from celery.schedules import crontab
import os

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'asterisk.settings')

app = Celery('asterisk')
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks(lambda: settings.INSTALLED_APPS)
app.conf.beat_schedule = {
    'add-every-day': {
        'task': 'office.tasks.disconnect_users',
        'schedule': crontab(**settings.CRONTAB_TASK)
    },
}

