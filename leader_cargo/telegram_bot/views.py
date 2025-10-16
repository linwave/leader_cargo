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

from .models import TelegramProfile
from .utils import send_telegram_message

BOT_TOKEN = settings.TELEGRAM_BOT_TOKEN
BOT_USERNAME = settings.TELEGRAM_BOT_USERNAME

@csrf_exempt  # Отключаем CSRF для вебхука
def webhook_handler(request):
    if request.method == 'POST':
        # Получаем данные из запроса
        data = json.loads(request.body)
        print("Received data:", data)

        # Обработка данных (например, текст сообщения)
        message = data.get('message', {}).get('text')
        print("Message text:", message)

        # Ответ Telegram'у
        return HttpResponse("OK")
    return HttpResponse("Method not allowed", status=405)

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
def telegram_webhook(request):
    if request.headers.get("X-Telegram-Bot-Api-Secret-Token") != settings.TELEGRAM_WEBHOOK_SECRET:
        return HttpResponseForbidden("bad secret")
    """
    Обрабатывает входящие сообщения от Telegram.
    """
    if request.method == 'POST':
        try:
            body = request.body.decode('utf-8')
            data = json.loads(body)

            chat_id = data['message']['chat']['id']
            text = data['message']['text']

            # Проверяем команду /start с параметром
            if text.startswith('/start'):
                token = text.split(' ')[1]  # Извлекаем токен из команды

                # Находим профиль по токену
                try:
                    telegram_profile = TelegramProfile.objects.get(token=token)

                    # Привязываем chat_id к пользователю
                    telegram_profile.chat_id = chat_id
                    telegram_profile.is_verified = True
                    telegram_profile.token = None  # Очищаем токен после использования
                    telegram_profile.save()

                    send_telegram_message(chat_id, "Ваш аккаунт успешно привязан!", BOT_TOKEN)
                    return JsonResponse({'status': 'ok'})

                except TelegramProfile.DoesNotExist:
                    send_telegram_message(chat_id, "Ошибка привязки. Неверный токен.", BOT_TOKEN)

            return JsonResponse({'status': 'error', 'message': 'Invalid command'})

        except Exception as e:
            print(f"Ошибка: {e}")
            return JsonResponse({'status': 'error', 'message': str(e)})

    return JsonResponse({'status': 'error', 'message': 'Invalid request method'})
