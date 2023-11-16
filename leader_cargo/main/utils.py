import datetime

from .models import ExchangeRates

menu = {
    'Курсы валют': {'title': 'Курсы валют', 'url_name': 'main:exchangerates', 'short_url': 'exchangerates'},
    'Сотрудники': {'title': 'Сотрудники', 'url_name': 'main:employees', 'short_url': 'employees'},
    'Система мониторинга': {'title': 'Система мониторинга', 'url_name': 'main:monitoring', 'short_url': 'monitoring'},
    'Калькулятор логистики': {'title': 'Калькулятор логистики', 'url_name': 'analytics:calculator', 'short_url': 'calculator'},
    'Учет грузов': {'title': 'Учет грузов', 'url_name': 'analytics:carrier', 'short_url': 'carrier'},
    'Клиенты': {'title': 'Клиенты', 'url_name': 'main:clients', 'short_url': 'clients'},
    'Заявки': {'title': 'Заявки', 'url_name': 'main:appeals', 'short_url': 'appeals'},
}

menu_super_admin = [
    menu['Курсы валют'],
    menu['Сотрудники'],
    menu['Система мониторинга'],
    menu['Калькулятор логистики'],
    menu['Учет грузов'],
    menu['Клиенты'],
    menu['Заявки'],
]

menu_rop = [
    menu['Система мониторинга'],
    # menu['Калькулятор логистики'],
    menu['Учет грузов'],
]

menu_admin = [
    menu['Курсы валют'],
    menu['Сотрудники'],
]

menu_manager = [
    menu['Система мониторинга'],
    # menu['Калькулятор логистики'],
    menu['Учет грузов'],
]

menu_buyer = [
    menu['Заявки'],
]

menu_client = [
    menu['Заявки'],
]

menu_logist = [
    menu['Учет грузов'],
    # menu['Калькулятор логистики'],
    menu['Курсы валют'],
]

initial_user_parameters = {
            'Супер Администратор': {'login_url': 'main:home', 'menu': menu_super_admin},
            'РОП': {'login_url': 'main:monitoring', 'menu': menu_rop},
            'Администратор': {'login_url': 'main:exchangerates', 'menu': menu_admin},
            'Логист': {'login_url': 'analytics:carrier', 'menu': menu_logist},
            'Менеджер': {'login_url': 'main:monitoring', 'menu': menu_manager},
            'Закупщик': {'login_url': 'main:appeals', 'menu': menu_buyer},
            'Клиент': {'login_url': 'main:appeals', 'menu': menu_client},
        }


class DataMixin:
    def get_user_context(self, **kwargs):
        context = kwargs
        if self.request.user.is_authenticated:
            context['menu'] = initial_user_parameters[self.request.user.role]['menu']
        context['last_currency'] = self.get_last_currency_dollar_and_yuan()
        context['today'] = datetime.datetime.date(datetime.datetime.now()).strftime("%d.%m.%y")
        return context

    @staticmethod
    def get_redirect_url_for_user(role):
        return initial_user_parameters[role]['login_url']

    @staticmethod
    def get_last_currency_dollar_and_yuan():
        try:
            curs = ExchangeRates.objects.filter(time_create__date=datetime.date.today())[:1][0]
            try:
                curs.yuan = str(format(float(curs.yuan), '.2f'))
            except TypeError:
                curs.yuan = ""
            try:
                curs.dollar = str(format(float(curs.dollar), '.2f'))
            except TypeError:
                curs.dollar = ""
            return curs
        except IndexError:
            return False


