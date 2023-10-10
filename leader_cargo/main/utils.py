import datetime

from .models import ExchangeRates

menu_super_admin = [
    # {'title': 'Главная', 'url_name': 'home'},
    # {'title': 'Авторизация', 'url_name': 'login'},
    {'title': 'Курсы валют', 'url_name': 'exchangerates'},
    {'title': 'Сотрудники', 'url_name': 'employees'},
    {'title': 'Система мониторинга', 'url_name': 'monitoring'},
    {'title': 'Клиенты', 'url_name': 'clients'},
    {'title': 'Заявки', 'url_name': 'appeals'},
]

menu_rop = [
    {'title': 'Система мониторинга', 'url_name': 'monitoring'},
    {'title': 'Учет грузов', 'url_name': 'carrier'},
]

menu_admin = [
    # {'title': 'Главная', 'url_name': 'home'},
    # {'title': 'Авторизация', 'url_name': 'login'},
    {'title': 'Курсы валют', 'url_name': 'exchangerates'},
    {'title': 'Сотрудники', 'url_name': 'employees'},
]

menu_manager = [
    # {'title': 'Главная', 'url_name': 'home'},
    # {'title': 'Авторизация', 'url_name': 'login'},
    {'title': 'Клиенты', 'url_name': 'clients'},
    {'title': 'Заявки', 'url_name': 'appeals'},
    {'title': 'Учет грузов', 'url_name': 'carrier'},
]

menu_buyer = [
    # {'title': 'Главная', 'url_name': 'home'},
    # {'title': 'Авторизация', 'url_name': 'login'},
    # {'title': 'Клиенты', 'url_name': 'clients'},
    {'title': 'Заявки', 'url_name': 'appeals'},
]

menu_client = [
    # {'title': 'Главная', 'url_name': 'home'},
    # {'title': 'Авторизация', 'url_name': 'login'},
    {'title': 'Заявки', 'url_name': 'appeals'},
]

menu_logist = [
    {'title': 'Учет грузов', 'url_name': 'carrier'},
]


def last_currency():
    try:
        curs = ExchangeRates.objects.filter(time_create__date=datetime.date.today()).order_by('-time_create')[:1][0]
        # print(ExchangeRates.objects.filter(time_create__date=datetime.datetime.today().date()))
        curs.yuan = str(format(float(curs.yuan), '.2f'))
        curs.dollar = str(format(float(curs.dollar), '.2f'))
        return curs
    except IndexError:
        return False


class DataMixin:

    def get_user_context(self, **kwargs):
        context = kwargs
        if self.request.user.is_authenticated:
            if self.request.user.role == 'Супер Администратор':
                context['menu'] = menu_super_admin
            elif self.request.user.role == 'РОП':
                context['menu'] = menu_rop
            elif self.request.user.role == 'Администратор':
                context['menu'] = menu_admin
            elif self.request.user.role == 'Логист':
                context['menu'] = menu_logist
            elif self.request.user.role == 'Менеджер':
                context['menu'] = menu_manager
            elif self.request.user.role == 'Закупщик':
                context['menu'] = menu_buyer
            elif self.request.user.role == 'Клиент':
                context['menu'] = menu_client
        context['last_currency'] = last_currency()
        context['today'] = datetime.datetime.date(datetime.datetime.now()).strftime("%d.%m.%y")
        return context
