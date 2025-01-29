from __future__ import absolute_import, unicode_literals

# Это гарантирует, что модуль celery будет загружен.
from .celery import app as celery_app

__all__ = ('celery_app',)