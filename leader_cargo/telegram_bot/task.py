from celery import shared_task
from django.utils.timezone import now
from .models import TelegramNotification
from .utils import send_telegram_message

@shared_task
def send_scheduled_telegram_notifications():
    """
    Отправляет запланированные уведомления.
    """
    notifications = TelegramNotification.objects.filter(scheduled_time__lte=now(), is_sent=False)
    for notification in notifications:
        # Отправляем уведомление через Telegram
        send_telegram_message(
            chat_id=notification.manager.telegram_profile.chat_id,
            text=f"Напоминание: {notification.notification_type} для лида {notification.lead.client_name}.")
        # Помечаем уведомление как отправленное
        notification.is_sent = True
        notification.save()
