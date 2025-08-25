import re

from django.conf import settings
from django.http import JsonResponse, HttpResponseNotAllowed
from django.utils import timezone
from rest_framework import generics
from datetime import datetime
import json
from analytics.models import CargoArticle
from django.views.decorators.csrf import csrf_exempt

from main.models import Calls, CustomUser, CRM_CHOICES
from .serializers import CargoArticleSerializer

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
class WomenAPIView(generics.ListAPIView):
    queryset = CargoArticle.objects.all()
    serializer_class = CargoArticleSerializer
