import logging
import re

from django.conf import settings
from django.contrib.auth import get_user_model
from django.http import JsonResponse, HttpResponseNotAllowed, HttpResponse
from django.utils import timezone
from rest_framework import generics
from datetime import datetime
import json
from analytics.models import CargoArticle
from django.views.decorators.csrf import csrf_exempt

from main.models import Calls, CustomUser, CRM_CHOICES
from telegram_bot.models import TelegramProfile
from telegram_bot.utils import send_telegram_message
from .serializers import CargoArticleSerializer

logger = logging.getLogger("inbound.calls")
API_TOKEN = getattr(settings, "API_ROSACCRED_TOKEN", None)

def _auth_ok(request):
    """Проверяем X-API-Key в заголовке."""
    client_token = request.headers.get("X-API-Key") or request.META.get('HTTP_X_API_KEY')
    return API_TOKEN and client_token and client_token == API_TOKEN

def _parse_date_ru(dstr):
    """
    Ожидаем строку даты в формате 'ДД.ММ.ГГГГ'. Возвращаем date или None.
    """
    if not dstr:
        return None
    try:
        return datetime.strptime(dstr.strip(), "%d.%m.%Y").date()
    except Exception:
        return None

def _calculate_work_years(date_reg):
    """
    Совместимо с прошлой логикой:
    - если даты нет -> (None, None)
    - считаем полные годы
    - минимум возвращаем 1 год
    - возвращаем date (не datetime)
    """
    if not date_reg:
        return None, None

    # Приведём к date на всякий случай
    if isinstance(date_reg, datetime):
        date_only = date_reg.date()
    else:
        date_only = date_reg

    today = timezone.localdate()
    years = today.year - date_only.year - ((today.month, today.day) < (date_only.month, date_only.day))
    return max(years, 1), date_only

def _normalize_phone(p):
    if not p:
        return ""
    return str(p).replace(" ", "").replace("+", "").strip()


PHONE_SPLIT_RE = re.compile(r'[,\;]+|\s{2,}')  # запятая/;/много пробелов


def _normalize_one_phone(p: str) -> str:
    """Нормализуем для сравнения: только цифры, 11 знаков, префикс 7."""
    if not p:
        return ""
    digits = re.sub(r'\D+', '', p)
    if not digits:
        return ""
    # Если 11 цифр и начинается с 8 -> заменить на 7
    if len(digits) == 11 and digits.startswith('8'):
        digits = '7' + digits[1:]
    # Если 10 цифр и начинается с 9 -> добавить 7
    if len(digits) == 10 and digits.startswith('9'):
        digits = '7' + digits
    return digits

def _parse_phones_any(payload_phone):
    """
    Принимает строку/список/None. Возвращает:
    - originals: список 'как есть' (обрезаем только крайние пробелы)
    - normalized: множество нормализованных цифро-строк для поиска дублей
    """
    originals = []
    normalized = set()

    if payload_phone is None:
        return originals, normalized

    if isinstance(payload_phone, list):
        raw_items = payload_phone
    else:
        # строка: порежем по запятым/;/двойным пробелам
        raw_items = [s for s in PHONE_SPLIT_RE.split(str(payload_phone)) if s.strip()]

    for item in raw_items:
        item_stripped = str(item).strip()
        if not item_stripped:
            continue
        originals.append(item_stripped)
        norm = _normalize_one_phone(item_stripped)
        if norm:
            normalized.add(norm)

    return originals, normalized

def _existing_normalized_phones():
    """
    Строим множество нормализованных телефонов из БД (по полю client_phone),
    разбивая по запятым/;/много пробелов.
    """
    existing = set()
    for cp in Calls.objects.values_list('client_phone', flat=True):
        if not cp:
            continue
        parts = [s for s in PHONE_SPLIT_RE.split(str(cp)) if s.strip()]
        for p in parts:
            norm = _normalize_one_phone(p.strip())
            if norm:
                existing.add(norm)
    return existing

def _pick_operator_round_robin():
    """
    Выбираем оператора круговым способом.
    Простой вариант: по последней записи Calls.
    Если операторов нет — вернём None.
    """
    operators = list(CustomUser.objects.filter(role='Оператор').order_by('id'))
    if not operators:
        return None
    # Найдём последнего оператора в последних созданных звонках
    last_call = Calls.objects.filter(operator__isnull=False).order_by('-id').first()
    if not last_call or last_call.operator not in operators:
        return operators[0]
    idx = operators.index(last_call.operator)
    return operators[(idx + 1) % len(operators)]

VALID_CRM = [c[0] for c in CRM_CHOICES]

def _create_call_one(payload):
    # ==== CRM ====
    crm_value = (payload.get('crm') or '').strip()
    if crm_value and crm_value not in VALID_CRM:
        return {"status": "skipped", "reason": "unsupported_crm", "crm": crm_value}

    # ==== ИМЯ ====
    parts = [
        (payload.get('last_name_director') or "").strip(),
        (payload.get('name_director') or "").strip(),
        (payload.get('otch_director') or "").strip(),
    ]
    client_name = " ".join([p for p in parts if p and p != '-']).strip()

    # ==== ТЕЛЕФОНЫ ====
    originals, normalized_incoming = _parse_phones_any(payload.get('phone'))
    if not client_name or not originals:
        return {"status": "skipped", "reason": "empty_name_or_phone", "phone": ""}

    combined_phones = ', '.join(originals)

    # ==== ДУБЛИКАТЫ ====
    existing_norm = _existing_normalized_phones()
    is_dup = any(n in existing_norm for n in normalized_incoming)
    if is_dup:
        return {"status": "duplicate", "phone": combined_phones}

    # ==== ДАТА ====
    raw_date = payload.get('date_registration')
    date_reg = _parse_date_ru(raw_date)
    work_years, date_reg = _calculate_work_years(date_reg)

    operator = _pick_operator_round_robin()

    call = Calls.objects.create(
        client_name=client_name,
        client_phone=combined_phones,
        status_call='Не обработано',
        date_call=timezone.now(),
        operator=operator,
        company_type=payload.get('type_company') or '',
        client_location=payload.get('address') or '',
        work_years=work_years,
        date_registration=date_reg,
        crm=crm_value or None,
    )
    return {"status": "created", "id": call.id, "phone": combined_phones, "crm": crm_value}

@csrf_exempt
def create_call_from_rosaccreditation(request):
    if request.method != "POST":
        return HttpResponseNotAllowed(["POST"])
    if not _auth_ok(request):
        return JsonResponse({"detail": "Unauthorized"}, status=401)

    try:
        payload = json.loads(request.body.decode("utf-8"))
    except Exception:
        return JsonResponse({"detail": "Invalid JSON"}, status=400)

    # Разрешим либо объект, либо список с 1 элементом
    if isinstance(payload, list):
        if not payload:
            return JsonResponse({"detail": "Empty list"}, status=400)
        payload = payload[0]
    elif not isinstance(payload, dict):
        return JsonResponse({"detail": "Expected JSON object"}, status=400)

    result = _create_call_one(payload)
    status = 201 if result.get("status") == "created" else 200
    return JsonResponse(result, status=status)

@csrf_exempt
def bulk_create_calls_from_rosaccreditation(request):
    """
    Принимает массив объектов и делает массовое создание.
    """
    if request.method != "POST":
        return HttpResponseNotAllowed(["POST"])
    if not _auth_ok(request):
        return JsonResponse({"detail": "Unauthorized"}, status=401)

    try:
        items = json.loads(request.body.decode("utf-8"))
    except Exception:
        return JsonResponse({"detail": "Invalid JSON"}, status=400)

    if not isinstance(items, list) or not items:
        return JsonResponse({"detail": "Expected non-empty JSON array"}, status=400)

    results = []
    for item in items:
        if not isinstance(item, dict):
            results.append({"status": "skipped", "reason": "not_object"})
            continue
        results.append(_create_call_one(item))

    created = sum(1 for r in results if r.get("status") == "created")
    duplicates = sum(1 for r in results if r.get("status") == "duplicate")
    skipped = sum(1 for r in results if r.get("status") == "skipped")

    return JsonResponse({
        "summary": {"created": created, "duplicates": duplicates, "skipped": skipped, "total": len(items)},
        "results": results
    }, status=207 if created and (duplicates or skipped) else (201 if created else 200))

def _client_ip(request):
    return (request.META.get('HTTP_X_FORWARDED_FOR') or request.META.get('REMOTE_ADDR') or '').split(',')[0].strip()

def _headers_snapshot(request, mask_keys=("cookie", "authorization", "x-api-key")):
    out = {}
    for k, v in request.headers.items():
        out[k] = "***" if k.lower() in mask_keys else v
    return out

def _is_browser_request(request):
    """Эвристика: наличие Origin/Sec-Fetch-Mode/Referer указывает на браузер."""
    if request.headers.get("Origin"):
        return True
    if request.headers.get("Sec-Fetch-Mode"):
        return True
    if request.headers.get("Referer"):
        return True
    return False

User = get_user_model()

def _notify_default_manager(call: Calls, crm_source: str, descr: str | None):
    """
    Отправляем уведомление одному фиксированному менеджеру:
    manager = User.objects.filter(pk=settings.CRM_DEFAULT_MANAGER_ID or 40).first()
    """
    if not TelegramProfile:
        return
    manager_id = getattr(settings, 'CRM_DEFAULT_MANAGER_ID', 40)
    manager = User.objects.filter(pk=manager_id).first()
    if not manager:
        return
    prof = TelegramProfile.objects.filter(user=manager, is_verified=True).first()
    if not prof or not getattr(prof, "chat_id", None):
        return
    text = (
        f"Новая заявка из {crm_source}\n"
        f"ID: {call.pk}\n"
        f"Клиент: {call.client_name or '—'}\n"
        f"Телефон: {call.client_phone}\n"
        f"Комментарий: {(descr or '—')}"
    )
    try:
        send_telegram_message(prof.chat_id, text, settings.TELEGRAM_BOT_TOKEN)
    except Exception as e:
        print(f"TG notify error: {e}")


def _parse_default_payload(payload):
    """Ожидает {"name": "...", "phone": "...|[...]", "comment": "..."}"""
    client_name = (payload.get('name') or '').strip()
    if not client_name:
        parts = [
            (payload.get('last_name') or '').strip(),
            (payload.get('first_name') or '').strip(),
            (payload.get('patronymic') or '').strip(),
        ]
        client_name = " ".join([p for p in parts if p]).strip()

    phones, _ = _parse_phones_any(payload.get('phone'))
    comment = (payload.get('comment') or '')[:600]
    return client_name, phones, comment


def _safe_get(d, *path, default=None):
    cur = d
    for key in path:
        if not isinstance(cur, dict) or key not in cur:
            return default
        cur = cur[key]
    return cur

def _collect_az_phones(payload):
    """
    Собираем телефоны из:
      - contact.presented_phones (список строк)
      - contact.phone1..phone10
      - current_call.called_phone
    Возвращаем список строк 'как есть' (без нормализации; нормализуем отдельно для дублей).
    """
    phones = []

    # presented_phones: список
    presented = _safe_get(payload, 'contact', 'presented_phones', default=[])
    if isinstance(presented, list):
        phones.extend([str(x).strip() for x in presented if x])

    # phone1..phone10
    contact = payload.get('contact') or {}
    for i in range(1, 11):
        v = contact.get(f'phone{i}')
        if v:
            phones.append(str(v).strip())

    # current_call.called_phone
    c_called = _safe_get(payload, 'current_call', 'called_phone')
    if c_called:
        phones.append(str(c_called).strip())

    # почистим пустые и дубликаты, сохранив порядок
    seen = set()
    uniq = []
    for p in phones:
        if p and p not in seen:
            uniq.append(p)
            seen.add(p)
    return uniq

def _build_az_comment(payload):
    """
    Сжато и информативно соберём все основные поля в один текстовый комментарий.
    """
    parts = []

    # CONTACT
    c = payload.get('contact') or {}
    cf_list = c.get('custom_fields') or []
    cf_str = "; ".join([f"{x.get('title') or x.get('name')}: {x.get('value')}" for x in cf_list if (x.get('value') is not None and str(x.get('value')).strip() != '')])

    parts.append("— CONTACT —")
    parts.append(f"id={c.get('id')}, name={c.get('name') or ''}")
    if c.get('email'):
        parts.append(f"email={c.get('email')}")
    if cf_str:
        parts.append(f"custom_fields: {cf_str}")

    # LEAD
    l = payload.get('lead') or {}
    l_cf = l.get('custom_fields') or []
    l_cf_str = "; ".join([f"{x.get('name')}: {x.get('value')}" for x in l_cf if (x.get('value') is not None and str(x.get('value')).strip() != '')])

    parts.append("\n— LEAD —")
    parts.append(f"id={l.get('id')}, status={l.get('lead_status_name') or ''}")
    if l.get('remark'):
        parts.append(f"remark={l.get('remark')}")
    if l.get('contact_person'):
        parts.append(f"contact_person={l.get('contact_person')}")
    if l.get('visit_plan_date_time'):
        parts.append(f"visit_plan={l.get('visit_plan_date_time')}")
    if l.get('created_at'):
        parts.append(f"created_at={l.get('created_at')}")
    if l.get('updated_at'):
        parts.append(f"updated_at={l.get('updated_at')}")
    if l_cf_str:
        parts.append(f"lead_custom_fields: {l_cf_str}")

    # CURRENT CALL
    cc = payload.get('current_call') or {}
    parts.append("\n— CURRENT_CALL —")
    parts.append(f"id={cc.get('id')}, result={cc.get('call_result_name') or ''}, duration={cc.get('call_duration')}")
    if cc.get('remark'):
        parts.append(f"remark={cc.get('remark')}")
    if cc.get('user_email'):
        parts.append(f"user={cc.get('user_email')}")
    if cc.get('created_at'):
        parts.append(f"created_at={cc.get('created_at')}")
    if cc.get('updated_at'):
        parts.append(f"updated_at={cc.get('updated_at')}")

    comment = "\n".join([p for p in parts if p])[:600]  # ограничиваем 600 символов
    return comment

def _parse_az_payload(payload):
    """Парсинг тела КЦ АЗ"""
    client_name = (
        _safe_get(payload, 'contact', 'name')
        or _safe_get(payload, 'lead', 'contact_person')
        or ''
    ).strip()

    if not client_name:
        parts = [
            (payload.get('last_name') or '').strip(),
            (payload.get('first_name') or '').strip(),
            (payload.get('patronymic') or '').strip(),
        ]
        client_name = " ".join([p for p in parts if p]).strip()

    phones = _collect_az_phones(payload)
    comment = _build_az_comment(payload)
    return client_name, phones, comment


def _corsify(resp: HttpResponse, origin: str | None, allowed_origins: set[str]):
    """
    Если запрос браузерный и origin разрешён — добавляем ACAO.
    Если allowed_origins пустой, трактуем как “разрешено всё” (не рекомендуется в проде).
    """
    if origin and (not allowed_origins or origin in allowed_origins or "*" in allowed_origins):
        resp["Access-Control-Allow-Origin"] = origin
        resp["Vary"] = "Origin"
    return resp

@csrf_exempt
def create_call_from_partner(request, hook):
    """
    Универсальный вебхук для партнёров.
    ЛОГИ: канал (browser/server), origin, referer, fetch-mode, IP, заголовки, сырое тело, итоги/ошибки.
    CORS: preflight + проверка allowed_origins.
    IP: optional allowlist/denylist per partner.
    """
    partners = getattr(settings, "API_PARTNERS", {})
    config = partners.get(hook)

    origin   = request.headers.get("Origin")
    referer  = request.headers.get("Referer")
    sfm      = request.headers.get("Sec-Fetch-Mode")
    ua       = request.headers.get("User-Agent", "")
    ip       = _client_ip(request)
    is_browser = _is_browser_request(request)
    is_preflight = (request.method == "OPTIONS")

    # Разрешённые origin’ы (для браузера)
    allowed_origins = set((config or {}).get("allowed_origins") or [])
    # Подмешать глобальные, если есть
    global_origins = getattr(settings, "CORS_ALLOWED_ORIGINS", [])
    allowed_origins.update(global_origins)

    # IP правила
    allowed_ips = set((config or {}).get("allowed_ips") or [])
    blocked_ips = set((config or {}).get("blocked_ips") or [])
    allow_no_origin = (config or {}).get("allow_no_origin", True)

    # Снимок заголовков и raw body для логов
    try:
        raw_body = request.body.decode("utf-8", errors="ignore")
    except Exception:
        raw_body = "<decode_error>"
    headers_dump = json.dumps(_headers_snapshot(request), ensure_ascii=False)

    logger.info(
        "INBOUND %s hook=%s channel=%s preflight=%s ip=%s origin=%s referer=%s fetch=%s ua=%s headers=%s body=%s",
        request.method, hook, ("browser" if is_browser else "server"), is_preflight,
        ip, origin, referer, sfm, ua, headers_dump, raw_body
    )

    # CORS preflight
    if is_preflight:
        resp = HttpResponse(status=204)
        resp["Access-Control-Allow-Methods"] = "POST, OPTIONS"
        resp["Access-Control-Allow-Headers"] = "Content-Type, X-API-Key"
        logger.info("INBOUND PRELIGHT OK hook=%s ip=%s origin=%s", hook, ip, origin)
        return _corsify(resp, origin, allowed_origins)

    # Метод
    if request.method != "POST":
        logger.warning("INBOUND WRONG_METHOD hook=%s method=%s ip=%s", hook, request.method, ip)
        return _corsify(HttpResponseNotAllowed(["POST", "OPTIONS"]), origin, allowed_origins)

    # Хук известен?
    if not config:
        logger.warning("INBOUND UNKNOWN_HOOK hook=%s ip=%s", hook, ip)
        return _corsify(JsonResponse({"detail": "Unknown hook"}, status=404), origin, allowed_origins)

    # Если это браузерный запрос, но origin не в whitelist — отклоняем.
    if is_browser:
        if origin is None:
            logger.warning("INBOUND CORS_NO_ORIGIN hook=%s ip=%s", hook, ip)
            return _corsify(JsonResponse({"detail": "CORS: missing Origin"}, status=403), origin, allowed_origins)
        if allowed_origins and origin not in allowed_origins and "*" not in allowed_origins:
            logger.warning("INBOUND CORS_FORBIDDEN hook=%s ip=%s origin=%s", hook, ip, origin)
            # Важно: даже при отказе добавим CORS, чтобы браузер увидел корректный ответ
            resp = JsonResponse({"detail": "CORS: origin not allowed"}, status=403)
            return _corsify(resp, origin, allowed_origins)
    else:
        # server-to-server без Origin
        if not allow_no_origin and origin is None:
            logger.warning("INBOUND NO_ORIGIN_DISALLOWED hook=%s ip=%s", hook, ip)
            return JsonResponse({"detail": "No-Origin requests disallowed"}, status=403)

    # IP deny
    if ip in blocked_ips:
        logger.warning("INBOUND BLOCKED_IP hook=%s ip=%s", hook, ip)
        return _corsify(JsonResponse({"detail": "IP blocked"}, status=403), origin, allowed_origins)

    # IP allow (если список задан)
    if allowed_ips and ip not in allowed_ips:
        logger.warning("INBOUND NOT_IN_ALLOWED_IPS hook=%s ip=%s", hook, ip)
        return _corsify(JsonResponse({"detail": "IP not allowed"}, status=403), origin, allowed_origins)

    # Токен (если требуется)
    if config.get("require_token", True):
        token = request.headers.get("X-API-Key") or request.META.get("HTTP_X_API_KEY")
        if not token or token != config.get("token"):
            logger.warning("INBOUND UNAUTHORIZED hook=%s ip=%s", hook, ip)
            return _corsify(JsonResponse({"detail": "Unauthorized"}, status=401), origin, allowed_origins)

    # Парсинг JSON
    try:
        payload = json.loads(raw_body or "{}")
    except Exception as e:
        logger.exception("INBOUND INVALID_JSON hook=%s ip=%s err=%s", hook, ip, e)
        return _corsify(JsonResponse({"detail": "Invalid JSON"}, status=400), origin, allowed_origins)

    # Парсер & CRM
    parser = config.get("parser", "default")
    crm_source = config.get("crm") or "Партнёр"

    try:
        if parser == "az":
            client_name, phones_originals, comment = _parse_az_payload(payload)
        else:
            client_name, phones_originals, comment = _parse_default_payload(payload)

        if not client_name or not phones_originals:
            logger.info("INBOUND SKIPPED empty_name_or_phone hook=%s ip=%s", hook, ip)
            return _corsify(JsonResponse({"status": "skipped", "reason": "empty_name_or_phone"}, status=200), origin, allowed_origins)

        # Дубли
        _, normalized_incoming = _parse_phones_any(phones_originals)
        existing_norm = _existing_normalized_phones()
        if any(n in existing_norm for n in normalized_incoming):
            logger.info("INBOUND DUPLICATE hook=%s ip=%s phones=%s", hook, ip, ", ".join(phones_originals))
            return _corsify(JsonResponse({"status": "duplicate", "phone": ", ".join(phones_originals)}, status=200), origin, allowed_origins)

        # Создаём
        call = Calls.objects.create(
            client_name=client_name,
            client_phone=", ".join(phones_originals),
            status_call="Не обработано",
            date_call=timezone.now(),
            crm=crm_source,
            description=comment,
        )

        logger.info(
            "INBOUND CREATED hook=%s channel=%s ip=%s origin=%s call_id=%s name=%s phones=%s crm=%s",
            hook, ("browser" if is_browser else "server"), ip, origin, call.id, client_name, ", ".join(phones_originals), crm_source
        )

        _notify_default_manager(call, crm_source=crm_source, descr=comment)

        return _corsify(JsonResponse({"status": "created", "id": call.id}, status=201), origin, allowed_origins)

    except Exception as e:
        logger.exception("INBOUND ERROR hook=%s ip=%s err=%s", hook, ip, e)
        return _corsify(JsonResponse({"detail": "Server error"}, status=500), origin, allowed_origins)

class WomenAPIView(generics.ListAPIView):
    queryset = CargoArticle.objects.all()
    serializer_class = CargoArticleSerializer

