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