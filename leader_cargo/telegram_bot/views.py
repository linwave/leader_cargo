import logging

from django.core.checks import messages
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.urls import reverse
from django.http import JsonResponse, HttpResponse, HttpResponseForbidden
from django.views.decorators.csrf import csrf_exempt
from django.contrib.sessions.models import Session
from django.contrib.auth import get_user_model
import json
import uuid
from django.conf import settings
from django.views.decorators.http import require_POST

from .models import TelegramProfile
from .utils import send_telegram_message

BOT_TOKEN = settings.TELEGRAM_BOT_TOKEN
BOT_USERNAME = settings.TELEGRAM_BOT_USERNAME

# @csrf_exempt  # Отключаем CSRF для вебхука
# def webhook_handler(request):
#     if request.method == 'POST':
#         # Получаем данные из запроса
#         data = json.loads(request.body)
#         print("Received data:", data)
#
#         # Обработка данных (например, текст сообщения)
#         message = data.get('message', {}).get('text')
#         print("Message text:", message)
#
#         # Ответ Telegram'у
#         return HttpResponse("OK")
#     return HttpResponse("Method not allowed", status=405)

@login_required
def link_telegram(request):
    """
    Генерирует ссылку для привязки Telegram.
    """
    telegram_profile, created = TelegramProfile.objects.get_or_create(user=request.user)

    if not telegram_profile.is_verified:
        # Генерация уникального токена
        token = str(uuid.uuid4())
        request.session['telegram_link_token'] = token
        request.session['telegram_user_id'] = request.user.id

        # Формируем ссылку
        bot_username = BOT_USERNAME
        link = f"https://t.me/{bot_username}?start={token}"

        context = {
            'link': link,
        }
        return render(request, 'link_telegram.html', context)
    else:
        return render(request, 'link_telegram.html', {'message': "Ваш Telegram уже привязан!"})

@login_required
def unlink_telegram(request):
    """
    Отвязывает Telegram-аккаунт от пользователя.
    """
    telegram_profile = request.user.telegram_profile
    telegram_profile.chat_id = None
    telegram_profile.is_verified = False
    telegram_profile.token = None
    telegram_profile.save()

    return redirect('main:home')  # Перенаправляем обратно на страницу профиля

@csrf_exempt
@require_POST
def telegram_webhook(request):
    # Проверяем секрет от Telegram
    if request.headers.get("X-Telegram-Bot-Api-Secret-Token") != settings.TELEGRAM_WEBHOOK_SECRET:
        return HttpResponseForbidden("bad secret")

    try:
        data = json.loads(request.body.decode("utf-8"))
    except Exception:
        return JsonResponse({'status': 'error', 'message': 'bad json'}, status=400)

    # Обрабатываем только нужные типы апдейтов
    message = (data.get('message') or {}).get('text')
    chat_id = ((data.get('message') or {}).get('chat') or {}).get('id')

    # /start <token> — привязка Telegram-профиля
    if message and message.startswith('/start'):
        parts = message.split(' ', 1)
        token = parts[1].strip() if len(parts) > 1 else None
        if token:
            from .models import TelegramProfile
            from .utils import send_telegram_message

            try:
                tp = TelegramProfile.objects.get(token=token)
                tp.chat_id = chat_id
                tp.is_verified = True
                tp.token = None
                tp.save()
                send_telegram_message(chat_id, "Ваш аккаунт успешно привязан!", settings.TELEGRAM_BOT_TOKEN)
                return JsonResponse({'status': 'ok'})
            except TelegramProfile.DoesNotExist:
                return JsonResponse({'status': 'error', 'message': 'bad link token'}, status=400)

    # здесь можешь добавить обработку других команд
    return JsonResponse({'status': 'ok'})
