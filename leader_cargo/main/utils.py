import datetime
from django.shortcuts import redirect
from django.contrib.auth.mixins import LoginRequiredMixin

from .models import ExchangeRates

categories = ['Курсы валют', 'Логистика', 'Мониторинг', 'Сотрудники', 'Клиенты', 'Заявки']

menu = {
    'Вход': {'title': 'Вход', 'url_name': 'main:login', 'short_url': 'login', 'display': True},

    'Учет грузов': {'title': 'Учет грузов', 'url_name': 'analytics:carrier', 'short_url': 'carrier', 'display': True,
                    'category_name': categories[1], 'menu_role': 'sub'},
    'Запрос логисту': {'title': 'Запрос ставки', 'url_name': 'analytics:logistic_requests', 'short_url': 'logistic_requests', 'display': False,
                       'category_name': categories[1], 'menu_role': 'sub'},
    'Запросы на просчет': {'title': 'Обработка запросов', 'url_name': 'analytics:logistic_requests', 'short_url': 'logistic_requests', 'display': False,
                           'category_name': categories[1], 'menu_role': 'sub'},
    'Калькулятор логистики': {'title': 'Калькулятор логистики', 'url_name': 'analytics:calculator', 'short_url': 'calculator', 'display': False,
                              'category_name': categories[1], 'menu_role': 'sub'},
    'Перевозчики': {'title': 'Перевозчики', 'url_name': 'analytics:carriers_list', 'short_url': 'carriers_list', 'display': True,
                    'category_name': categories[1], 'menu_role': 'sub'},

    'Курсы валют': {'title': 'Курсы валют', 'url_name': 'main:exchangerates', 'short_url': 'exchangerates', 'display': True,
                    'category_name': categories[0], 'menu_role': 'basic'},
    'Установка курса валют': {'title': 'Установка курса валют', 'url_name': 'main:create_exchangerates', 'short_url': 'create_exchangerates', 'display': True,
                              'category_name': categories[0], 'menu_role': 'sub'},

    'Мониторинг': {'title': 'Мониторинг', 'url_name': 'main:monitoring', 'short_url': 'monitoring', 'display': True,
                   'category_name': categories[2], 'menu_role': 'basic'},
    'Таблица результатов': {'title': 'Таблица результатов', 'url_name': 'main:monitoring_leaderboard', 'short_url': 'monitoring_leaderboard', 'display': True,
                            'category_name': categories[2], 'menu_role': 'sub'},

    'Сотрудники': {'title': 'Сотрудники', 'url_name': 'main:employees', 'short_url': 'employees', 'display': True,
                   'category_name': categories[3], 'menu_role': 'basic'},
    'Регистрация сотрудника': {'title': 'Регистрация сотрудника', 'url_name': 'main:create_employees', 'short_url': 'create_employees', 'display': True,
                               'category_name': categories[3], 'menu_role': 'sub'},

    'Клиенты': {'title': 'Клиенты', 'url_name': 'main:clients', 'short_url': 'clients', 'display': False,
                'category_name': categories[4], 'menu_role': 'basic'},
    'Создание клиента': {'title': 'Создание клиента', 'url_name': 'main:create_client', 'short_url': 'create_client', 'display': False,
                         'category_name': categories[4], 'menu_role': 'sub'},

    'Заявки': {'title': 'Клиенты', 'url_name': 'main:appeals', 'short_url': 'appeals', 'display': False,
               'category_name': categories[5], 'menu_role': 'basic'},
    'Создание заявки': {'title': 'Создание клиента', 'url_name': 'main:create_appeal', 'short_url': 'create_appeal', 'display': False,
                        'category_name': categories[5], 'menu_role': 'sub'},
}

menu_super_admin = [
    {
        'name': categories[0],
        'basic': menu['Курсы валют'],
        'sub_menu': [menu['Установка курса валют']]
    },
    {
        'name': categories[1],
        'basic': menu['Учет грузов'],
        'sub_menu': [menu['Запросы на просчет'], menu['Калькулятор логистики'], menu['Перевозчики']]
    },
    {
        'name': categories[2],
        'basic': menu['Мониторинг'],
        'sub_menu': [menu['Таблица результатов']]
    },
    {
        'name': categories[3],
        'basic': menu['Сотрудники'],
        'sub_menu': [menu['Регистрация сотрудника']]
    },
    {
        'name': categories[4],
        'basic': menu['Клиенты'],
        'sub_menu': [menu['Создание клиента']]
    },
    {
        'name': categories[5],
        'basic': menu['Заявки'],
        'sub_menu': [menu['Создание заявки']]
    }
]
menu_rop = [
    {
        'name': categories[1],
        'basic': menu['Учет грузов'],
        'sub_menu': [menu['Запрос логисту']]
    },
    {
        'name': categories[2],
        'basic': menu['Мониторинг'],
        'sub_menu': [menu['Таблица результатов']]
    },
    # {
    #     'name': categories[3],
    #     'basic': menu['Сотрудники'],
    #     'sub_menu': [menu['Регистрация сотрудника']]
    # },
    # {
    #     'name': categories[4],
    #     'basic': menu['Клиенты'],
    #     'sub_menu': [menu['Создание клиента']]
    # },
    # {
    #     'name': categories[5],
    #     'basic': menu['Заявки'],
    #     'sub_menu': [menu['Создание заявки']]
    # }
]
menu_admin = [
    {
        'name': categories[0],
        'basic': menu['Курсы валют'],
        'sub_menu': [menu['Установка курса валют']]
    },
    {
        'name': categories[3],
        'basic': menu['Сотрудники'],
        'sub_menu': [menu['Регистрация сотрудника']]
    }
]

menu_manager = [
    {
        'name': categories[1],
        'basic': menu['Учет грузов'],
        'sub_menu': [menu['Запрос логисту']]
    },
    {
        'name': categories[2],
        'basic': menu['Таблица результатов'],
        'sub_menu': []
    },
    # {
    #     'name': categories[5],
    #     'basic': menu['Заявки'],
    #     'sub_menu': [menu['Создание заявки']]
    # }
]
menu_buyer = [
    {
        'name': categories[5],
        'basic': menu['Заявки'],
        'sub_menu': [menu['Создание заявки']]
    }
]

menu_client = [
    {
        'name': categories[5],
        'basic': menu['Заявки'],
        'sub_menu': [menu['Создание заявки']]
    }
]

menu_logist = [
    {
        'name': categories[0],
        'basic': menu['Курсы валют'],
        'sub_menu': [menu['Установка курса валют']]
    },
    {
        'name': categories[1],
        'basic': menu['Учет грузов'],
        # 'sub_menu': [menu['Запросы на просчет']]
        'sub_menu': [menu['Запросы на просчет'], menu['Перевозчики']]
    },
    {
        'name': categories[2],
        'basic': menu['Таблица результатов'],
        'sub_menu': []
    }
]

initial_user_parameters = {
    'Супер Администратор': {'login_url': 'main:home', 'menu': menu_super_admin},
    'РОП': {'login_url': 'main:monitoring', 'menu': menu_rop},
    'Администратор': {'login_url': 'main:exchangerates', 'menu': menu_admin},
    'Логист': {'login_url': 'analytics:carrier', 'menu': menu_logist},
    'Менеджер': {'login_url': 'main:monitoring_leaderboard', 'menu': menu_manager},
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
                curs.yuan_cash_M = str(format(float(curs.yuan_cash_M), '.2f'))
            except TypeError:
                curs.yuan_cash_M = ""
            try:
                curs.yuan_cash_K = str(format(float(curs.yuan_cash_K), '.2f'))
            except TypeError:
                curs.yuan_cash_K = ""
            try:
                curs.yuan = str(format(float(curs.yuan), '.2f'))
            except TypeError:
                curs.yuan = ""
            try:
                curs.yuan_non_cash = str(format(float(curs.yuan_non_cash), '.2f'))
            except TypeError:
                curs.yuan_non_cash = ""
            try:
                curs.dollar = str(format(float(curs.dollar), '.2f'))
            except TypeError:
                curs.dollar = ""
            return curs
        except IndexError:
            return False


class MyLoginMixin(LoginRequiredMixin):
    role_have_perm = None

    def get_role_have_perm(self):
        return self.role_have_perm

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return self.handle_no_permission()
        else:
            if request.user.role in self.get_role_have_perm():
                return super().dispatch(request, *args, **kwargs)
            return redirect(self.get_redirect_url_for_user(role=request.user.role))

    @staticmethod
    def get_redirect_url_for_user(role):
        return initial_user_parameters[role]['login_url']
