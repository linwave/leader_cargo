import uuid

from django.db import models
from django.contrib.auth import get_user_model


class TelegramProfile(models.Model):
    user = models.OneToOneField(get_user_model(), on_delete=models.CASCADE, related_name='telegram_profile')
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
