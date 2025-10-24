# telegram_bot/management/commands/set_telegram_webhook.py
from django.core.management.base import BaseCommand
from django.conf import settings
import requests

class Command(BaseCommand):
    help = "Set Telegram webhook with secret token"

    def add_arguments(self, parser):
        parser.add_argument('--url', required=True, help='Webhook URL')

    def handle(self, *args, **opts):
        token = settings.TELEGRAM_BOT_TOKEN
        secret = settings.TELEGRAM_WEBHOOK_SECRET
        url = f"https://api.telegram.org/bot{token}/setWebhook"
        resp = requests.post(url, data={
            "url": opts['url'],
            "secret_token": secret,
            "drop_pending_updates": True,
        }, timeout=15)
        self.stdout.write(resp.text)