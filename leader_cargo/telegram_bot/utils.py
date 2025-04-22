import requests

def send_telegram_message(chat_id, text, bot_token):
    """
    Отправляет сообщение в Telegram.
    """
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    payload = {
        'chat_id': chat_id,
        'text': text
    }
    response = requests.post(url, data=payload)
    if response.status_code != 200:
        print(f"Ошибка при отправке сообщения: {response.text}")
