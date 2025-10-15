import uuid
from django.conf import settings
from django.db import models
from django.contrib.auth import get_user_model


class TelegramProfile(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='telegram_profile')
    chat_id = models.BigIntegerField(unique=True, null=True, blank=True, verbose_name="Chat ID")
    is_verified = models.BooleanField(default=False, verbose_name="Привязан ли Telegram")
    token = models.CharField(max_length=36, unique=True, null=True, blank=True, verbose_name="Токен для привязки")

    def generate_token(self):
        """
        Генерирует уникальный токен для привязки Telegram.
        """
        self.token = str(uuid.uuid4())
        self.save()

    def __str__(self):
        return f"Telegram Profile for {self.user}"


class TelegramNotification(models.Model):
    lead = models.ForeignKey('main.Leads', on_delete=models.CASCADE, related_name='notifications')
    manager = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='telegram_notifications')

    NOTIFY_CHOICES = [
        ('10_min_before', 'За 10 минут до звонка'),
        ('exact_time', 'В точное время'),
        # (оставлю старые для совместимости, если где-то использовались)
        ('30_min_before', 'За 30 минут до звонка'),
        ('next_day_9am', 'На следующий день в 9:00'),
    ]
    notification_type = models.CharField(max_length=50, choices=NOTIFY_CHOICES)
    scheduled_time = models.DateTimeField(verbose_name="Время отправки")
    is_sent = models.BooleanField(default=False, verbose_name="Отправлено")

    # Храним id запланированной celery-задачи, чтобы можно было revoke()
    task_id = models.CharField(max_length=100, blank=True, null=True, verbose_name='Celery task id')

    def __str__(self):
        return f"{self.notification_type} для {self.manager} на {self.scheduled_time}"

