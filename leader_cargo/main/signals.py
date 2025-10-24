# main/signals.py
from datetime import timedelta
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone
from celery import current_app

from .models import Leads
from telegram_bot.models import TelegramNotification
from telegram_bot.tasks import send_tg_notification_task

def _revoke_pending(notifs_qs):
    """
    Отменяет запланированные celery-задачи по id и удаляет записи.
    """
    for n in notifs_qs:
        if n.task_id:
            try:
                current_app.control.revoke(n.task_id, terminate=False)
            except Exception:
                pass
    notifs_qs.delete()

def _schedule_one(lead: Leads, notif_type: str, when_dt):
    """
    Создаёт запись в БД и планирует celery-задачу на указанное время (aware).
    """
    notif = TelegramNotification.objects.create(
        lead=lead,
        manager=lead.manager,
        notification_type=notif_type,
        scheduled_time=when_dt
    )

    # Celery принимает ETA в UTC
    eta_utc = when_dt.astimezone(timezone.utc)
    async_res = send_tg_notification_task.apply_async(args=[notif.pk], eta=eta_utc)
    notif.task_id = async_res.id
    notif.save(update_fields=['task_id'])

@receiver(post_save, sender=Leads)
def leads_post_save(sender, instance: Leads, created, **kwargs):
    """
    При любом сохранении лида пересобираем уведомления, если у лида есть дата и менеджер.
    """
    # Сначала чистим все неподтверждённые старые уведомления по этому лиду
    _revoke_pending(instance.notifications.filter(is_sent=False))

    # Ничего планировать, если не задано поле/нет менеджера/время уже прошло
    if not instance.manager or not instance.date_next_call_manager:
        return

    call_dt = instance.date_next_call_manager
    now = timezone.now()
    if call_dt <= now:
        return

    # -10 минут
    ten_min_before = call_dt - timedelta(minutes=10)
    if ten_min_before > now:
        _schedule_one(instance, '10_min_before', ten_min_before)

    # в точное время
    _schedule_one(instance, 'exact_time', call_dt)
