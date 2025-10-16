import logging
import os
import re

# Базовые шаблоны для токенов/секретов
PATTERNS = [
    re.compile(r"bot\d{6,}:[A-Za-z0-9_-]{20,}"),  # Telegram bot token
    re.compile(r"(?i)(token|apikey|secret|key|password)=([A-Za-z0-9._-]+)"),
    re.compile(r"Authorization:\s*Bearer\s+[A-Za-z0-9._-]+"),
]

# Маскируем конкретные значения из окружения, если вдруг попадут в лог
for k, v in os.environ.items():
    lk = k.lower()
    if any(s in lk for s in ["token", "secret", "key", "password"]):
        if v:
            PATTERNS.append(re.compile(re.escape(v)))

class RedactingFormatter(logging.Formatter):
    def format(self, record):
        s = super().format(record)
        for pat in PATTERNS:
            s = pat.sub("***", s)
        return s