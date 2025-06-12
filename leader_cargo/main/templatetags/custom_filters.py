# templatetags/custom_filters.py
from django import template

register = template.Library()


@register.filter(name='add_slashes')
def add_slashes(value):
    if isinstance(value, str):
        return f"/{value}/"
    return value

@register.filter
def remove_param(query_string, param_to_remove):
    # Разделяем строку запроса на параметры
    params = query_string.split('&')
    # Фильтруем параметры, исключая те, которые начинаются с param_to_remove
    filtered_params = [p for p in params if not p.startswith(param_to_remove + '=')]
    # Соединяем оставшиеся параметры обратно в строку
    return '&'.join(filtered_params)


@register.filter
def urlencode_after_remove(query_dict, param_to_remove):
    new_query_dict = query_dict.copy()
    if param_to_remove in new_query_dict:
        del new_query_dict[param_to_remove]
    return new_query_dict.urlencode()

@register.filter
def pluralize_ru(value, forms):
    # "год,года,лет"
    one, few, many = forms.split(',')
    n = abs(int(value))
    if n % 10 == 1 and n % 100 != 11:
        return one
    elif 2 <= n % 10 <= 4 and not (12 <= n % 100 <= 14):
        return few
    else:
        return many

@register.filter
def split_by_comma(value):
    if not value:
        return []
    return [v.strip() for v in value.split(',')]