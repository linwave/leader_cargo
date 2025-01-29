from __future__ import absolute_import, unicode_literals
import os
from celery import Celery

# Установите переменную окружения для настроек Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'leader_cargo.settings')

app = Celery('leader_cargo')

# Используйте настройки Django для конфигурации Celery
app.config_from_object('django.conf:settings', namespace='CELERY')

# Автоматическое обнаружение задач в приложениях Django
app.autodiscover_tasks()

@app.task(bind=True)
def debug_task(self):
    print(f'Request: {self.request!r}')
