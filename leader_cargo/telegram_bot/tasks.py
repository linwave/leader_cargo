# telegram_bot/tasks.py
from celery import shared_task
from django.utils import timezone
from django.conf import settings

from .models import TelegramNotification, TelegramProfile
import requests

def _send_telegram_message(chat_id: int, text: str, bot_token: str):
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    payload = {'chat_id': chat_id, 'text': text, 'parse_mode': 'HTML', 'disable_web_page_preview': True}
    r = requests.post(url, data=payload, timeout=10)
    r.raise_for_status()

def _build_lead_message(lead):
    parts = ["📞 <b>Напоминание по ЛИДу</b>"]
    if lead.client_name:
        parts.append(f"👤 {lead.client_name}")
    if lead.client_phone:
        parts.append(f"📱 {lead.client_phone}")
    if lead.client_location:
        parts.append(f"📍 {lead.client_location}")
    parts.append(f"🔖 Статус: {lead.status_manager or '—'}")
    if lead.date_next_call_manager:
        parts.append(f"🕒 Следующий звонок: {timezone.localtime(lead.date_next_call_manager).strftime('%d.%m.%Y %H:%M')}")

    if lead.description_manager:
        parts.append(f"📝 Заметка:\n{lead.description_manager}")

    # Добавь ссылку на карточку лида, если есть именованный url
    # from django.urls import reverse
    # try:
    #     url = reverse('main:card_lead', kwargs={'lead_id': lead.pk})
    #     parts.append(f"🔗 Открыть: {url}")
    # except Exception:
    #     pass

    return "\n".join(parts)

@shared_task(bind=True)
def send_tg_notification_task(self, notif_id: int):
    notif = TelegramNotification.objects.select_related('lead', 'manager').filter(pk=notif_id, is_sent=False).first()
    if not notif:
        return

    manager = notif.manager
    # Берём chat_id из TelegramProfile
    profile = getattr(manager, 'telegram_profile', None)
    chat_id = getattr(profile, 'chat_id', None) if profile else None
    if not chat_id:
        return  # нет chat_id — тихо пропустим

    text = _build_lead_message(notif.lead)
    _send_telegram_message(chat_id, text, settings.TELEGRAM_BOT_TOKEN)

    notif.is_sent = True
    notif.save(update_fields=['is_sent'])
