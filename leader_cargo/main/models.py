import datetime
import logging
import re
import sqlite3

import pandas as pd
from django.contrib.auth.models import AbstractUser
from django.db import models, transaction
from django.db.models import Q, Count, Subquery, OuterRef
from django.urls import reverse
from django.utils import timezone
from django.utils.timezone import localtime, now
from simple_history.models import HistoricalRecords

from telegram_bot.models import TelegramNotification

logger = logging.getLogger(__name__)

from django.db import models


def find_best_matches(col_name, possible_names):
    return any(name.lower() in col_name.lower() for name in possible_names)


class MaintenanceMode(models.Model):
    is_enabled = models.BooleanField(default=False, verbose_name="Включить режим обслуживания")
    message = models.TextField(
        default="Идут технические работы, пожалуйста, подождите.",
        verbose_name="Сообщение для пользователей"
    )

    def __str__(self):
        return "Режим обслуживания" if self.is_enabled else "Режим обслуживания выключен"

    class Meta:
        verbose_name = "Режим обслуживания"
        verbose_name_plural = "Режимы обслуживания"


class CustomUser(AbstractUser):
    towns = [
        ('Москва', 'Москва'),
        ('Краснодар', 'Краснодар'),
    ]
    roles = [
        ('Супер Администратор', 'Супер Администратор'),
        ('РОП', 'РОП'),
        ('Администратор', 'Администратор'),
        ('Бухгалтер', 'Бухгалтер'),
        ('Логист', 'Логист'),
        ('Логист Китай', 'Логист Китай'),
        ('Менеджер', 'Менеджер'),
        ('Оператор', 'Оператор'),
        ('Закупщик', 'Закупщик'),
        ('Клиент', 'Клиент')
    ]
    statuses = [
        (True, 'Активен'),
        (False, 'Заблокирован')
    ]
    first_name = models.CharField('Имя/ФИО', max_length=150, blank=False)
    phone = models.CharField('Телефон', max_length=50, unique=True)
    role = models.CharField(max_length=50, choices=roles, default='Менеджер', verbose_name='Роль')
    patronymic = models.CharField('Отчество', max_length=50, blank=True)
    town = models.CharField('Город', max_length=50, choices=towns, default='Москва')
    description = models.CharField('Описание', max_length=240, blank=True)
    manager = models.IntegerField('Менеджер', blank=True, null=True)
    pass_no_sha = models.CharField('Доп.пароль', max_length=200, blank=True)
    # manager_monthly_net_profit_plan = models.CharField('План по чистой прибыли в месяц', max_length=200, blank=True, null=True)

    time_create = models.DateTimeField(auto_now_add=True, verbose_name='Дата создания')
    time_update = models.DateTimeField(auto_now=True, verbose_name='Дата изменения')
    status = models.BooleanField(default=True, choices=statuses, verbose_name='Статус')

    class Meta:
        verbose_name = 'Пользователи'
        verbose_name_plural = 'Пользователи'
        ordering = ['-status', 'town', '-role', '-time_create']

    def __str__(self):
        return f'{self.last_name} {self.first_name}'

    @classmethod
    def get_managers(cls):
        return cls.objects.filter(role__in=['Менеджер'])

    @classmethod
    def get_managers_and_operators(cls):
        return cls.objects.filter(role__in=['Менеджер', 'Оператор'])

    @classmethod
    def get_managers_and_operators_and_rops(cls):
        return cls.objects.filter(role__in=['Менеджер', 'Оператор', 'РОП'])
    @classmethod
    def get_new_leads_count_for_all_managers(cls):
        managers_with_new_calls = cls.objects.filter(role='Менеджер').annotate(
            new_leads_count=Count('manager_leads', filter=models.Q(manager_leads__status_manager='Новая'))
        )

        return managers_with_new_calls

    @classmethod
    def get_new_in_work_leads_count_for_all_managers(cls):
        managers_with_calls = cls.objects.filter(role='Менеджер').annotate(
            new_calls_count=Count('manager_leads', filter=Q(manager_leads__status_manager='Новая')),
            in_progress_calls_count=Count('manager_leads', filter=Q(manager_leads__status_manager='В работе'))
        )

        return managers_with_calls

    @classmethod
    def get_all_status_leads_count_for_all_managers(cls):
        statuses = [status for status, _ in Leads.statuses_manager]

        annotations = {
            f"{status.lower().replace(' ', '_')}_count": Count(
                'manager_leads',
                filter=Q(manager_leads__status_manager=status)
            ) for status in statuses
        }

        return cls.objects.filter(role='Менеджер').annotate(**annotations)

    @classmethod
    def get_calls_count_for_all_managers(cls):
        managers_with_calls = cls.objects.filter(role='Менеджер').annotate(
            new_calls_count=Count('manager_calls', filter=models.Q(manager_leads__status_manager__in=['Новая', 'В работе']))
        )

        return managers_with_calls

    def get_absolute_url_client(self):
        return reverse('main:card_client', kwargs={'client_id': self.pk})

    def get_absolute_url_employee(self):
        return reverse('main:card_employees', kwargs={'employee_id': self.pk})

    def get_net_profit_to_the_company(self):
        for reports in self.managersreports_set.all():
            return reports

    def get_FI(self):
        if self.last_name and self.first_name:
            return f'{self.last_name} {self.first_name}'
        return ""

    def get_new_calls_count(self):
        return Calls.objects.filter(status_call='Новая', manager=self).count()


# class Employees(models.Model):
#     towns = [
#         ('Москва', 'Москва'),
#         ('Краснодар', 'Краснодар'),
#         ('Екатеринбург', 'Екатеринбург'),
#     ]
#     roles = [
#         ('Администратор', 'Администратор'),
#         ('Менеджер', 'Менеджер'),
#         ('Закупщик', 'Закупщик')
#     ]
#     statuses = [
#         (True, 'Активен'),
#         (False, 'Заблокирован')
#     ]
#     phone = models.CharField('Телефон', max_length=50)
#     password = models.CharField('Пароль', max_length=50)
#     role = models.CharField(max_length=50, choices=roles, default='Менеджер')
#     surname = models.CharField('Фамилия', max_length=50)
#     name = models.CharField('Имя', max_length=50)
#     patronymic = models.CharField('Отчество', max_length=50)
#     town = models.CharField(max_length=50, choices=towns, default='Москва')
#     time_create = models.DateTimeField(auto_now_add=True)
#     time_update = models.DateTimeField(auto_now=True)
#     status = models.BooleanField(default=True, choices=statuses)
#
#     def __str__(self):
#         return f"{self.surname} {self.name} {self.patronymic}"
#
#     class Meta:
#         verbose_name = 'Список сотрудников'
#         verbose_name_plural = 'Список сотрудников'
#
#     def get_absolute_url(self):
#         return reverse('card_employees', kwargs={'employee_id': self.pk})
#
#


class Clients(models.Model):
    phone = models.CharField('Телефон', max_length=50, unique=True)
    name = models.CharField('ФИО', max_length=50)
    description = models.CharField('Описание', max_length=150)

    manager = models.ForeignKey(CustomUser, verbose_name='Ответственный менеджер', on_delete=models.SET_NULL, blank=True, null=True, related_name="clients")

    time_create = models.DateTimeField(auto_now_add=True)
    time_update = models.DateTimeField(auto_now=True)
    status = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.phone} {self.name}"

    class Meta:
        verbose_name = 'Список клиентов'
        verbose_name_plural = 'Список клиентов'

    def get_absolute_url(self):
        return reverse('card_client', kwargs={'client_id': self.pk})


class ExchangeRates(models.Model):
    yuan_cash_M = models.FloatField(verbose_name='Курс ¥ Наличка Москва', blank=True, null=True)
    yuan_cash_K = models.FloatField(verbose_name='Курс ¥ Наличка Краснодар', blank=True, null=True)
    yuan = models.FloatField(verbose_name='Курс ¥ на карты', blank=True, null=True)
    yuan_non_cash = models.FloatField(verbose_name='Курс ¥ по безналичному р/с', blank=True, null=True)
    dollar = models.FloatField(verbose_name='Курс $', blank=True, null=True)
    time_create = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.time_create} Наличка Москва - {self.yuan_cash_M} Наличка Краснодар - {self.yuan_cash_K}" \
               f"На карты - {self.yuan} По безналичному р/с - {self.yuan_non_cash} Курс $ - {self.dollar}"

    class Meta:
        verbose_name = 'Курсы валют'
        verbose_name_plural = 'Курсы валют'
        ordering = ['-time_create']


class Appeals(models.Model):
    client = models.IntegerField('ID клиента', blank=True, null=True)
    manager = models.IntegerField('ID менеджера', blank=True, null=True)
    buyer = models.IntegerField('ID закупщика', blank=True, null=True)
    tag = models.CharField('Тег заявки', max_length=50, unique=True)
    logistic_price = models.CharField(verbose_name='Логистика', max_length=50, blank=True, null=True)
    insurance_price = models.CharField(verbose_name='Страховка', max_length=50, blank=True, null=True)
    packaging_price = models.CharField(verbose_name='Упаковка', max_length=50, blank=True, null=True)
    prr_price = models.CharField(verbose_name='ПРР', max_length=50, blank=True, null=True)
    status = models.CharField('Статус заявки', max_length=50, blank=True, null=True)
    time_create = models.DateTimeField(auto_now_add=True)
    time_update = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.tag}"

    class Meta:
        verbose_name = 'Список заявок'
        verbose_name_plural = 'Список заявок'
        ordering = ['-time_create']

    def get_absolute_url(self):
        return reverse('main:card_appeal', kwargs={'appeal_id': self.pk})

    def get_appeal_photo(self):
        for good in self.goods_set.all():
            if good.photo_good:
                return good.photo_good

    def get_client(self):
        return CustomUser.objects.get(pk=self.client)


class Goods(models.Model):
    name = models.CharField('Название товара', max_length=128, blank=False, null=True)
    photo_good = models.ImageField(verbose_name='Фото товара', upload_to='photos/goods/%Y/%m/%d/', blank=True, null=True)
    link_url = models.CharField('Ссылка на товар', max_length=500, blank=True, null=True)
    product_description = models.CharField('Описание товара', max_length=1024, blank=True, null=True)
    quantity = models.CharField(verbose_name='Количество', max_length=50, blank=True, null=True)
    price_rmb = models.CharField(verbose_name='Цена товара в Китае в юанях', max_length=50, blank=True, null=True)
    price_purchase = models.CharField(verbose_name='Закупочная цена', max_length=50, blank=True, null=True)
    price_site = models.CharField(verbose_name='Цена на сайте', max_length=50, blank=True, null=True)
    price_delivery = models.CharField(verbose_name='Стоимость доставки', max_length=50, blank=True, null=True)
    price_delivery_real = models.CharField(verbose_name='Стоимость доставки реальная', max_length=50, blank=True, null=True)
    price_delivery_rf = models.CharField(verbose_name='Стоимость доставки в РФ', max_length=50, blank=True, null=True)
    price_delivery_rf_real = models.CharField(verbose_name='Стоимость доставки в РФ реальная', max_length=50, blank=True, null=True)

    appeal_id = models.ForeignKey('Appeals', on_delete=models.PROTECT, blank=True, null=True)
    time_create = models.DateTimeField(auto_now_add=True)
    time_update = models.DateTimeField(auto_now=True)
    status = models.BooleanField(default=True, blank=True, null=True)

    def __str__(self):
        return f"{self.name}"

    class Meta:
        verbose_name = 'Список товаров'
        verbose_name_plural = 'Список товаров'

    def get_result_yuan(self):
        result = 0
        if self.price_rmb and self.quantity:
            result = result + float(self.price_rmb.replace(' ', '').replace(',', '.')) * float(self.quantity.replace(' ', '').replace(',', '.'))
        if self.price_delivery:
            result = result + float(self.price_delivery.replace(' ', '').replace(',', '.'))
        return result

    def get_result_self_yuan(self):
        result = 0
        if self.price_purchase and self.quantity:
            result = result + float(self.price_purchase.replace(' ', '').replace(',', '.')) * float(self.quantity.replace(' ', '').replace(',', '.'))
        if self.price_delivery_real:
            result = result + float(self.price_delivery_real.replace(' ', '').replace(',', '.'))
        return result

    def company_profit_yuan(self):
        result = 0
        if self.get_result_yuan() and self.get_result_self_yuan():
            result = self.get_result_yuan() - self.get_result_self_yuan()
        return result

    def company_profit_dollar(self):
        result = 0
        if self.price_delivery_rf and self.price_delivery_rf_real:
            result = result + float(self.price_delivery_rf.replace(' ', '').replace(',', '.')) - float(self.price_delivery_rf_real.replace(' ', '').replace(',', '.'))
        return result


class ManagersReports(models.Model):
    net_profit_to_the_company = models.CharField('Чистая прибыль в компанию', max_length=128, blank=True, null=True)
    raised_funds_to_the_company = models.CharField('Привлеченные средства в компанию', max_length=128, blank=True, null=True)
    number_of_new_clients_attracted = models.CharField('Количество привлеченных новых клиентов', max_length=128, blank=True, null=True)
    number_of_applications_to_buyers = models.CharField('Количество заявок закупщикам', max_length=128, blank=True, null=True)
    amount_of_issued_CP = models.CharField('Сумма выставленных КП', max_length=128, blank=True, null=True)
    number_of_incoming_quality_applications = models.CharField('Количество входящих качественных заявок', max_length=128, blank=True, null=True)
    number_of_completed_transactions_based_on_orders = models.CharField('Количество совершенных сделок по заявкам', max_length=128, blank=True, null=True)
    number_of_shipments_sent = models.CharField('Количество отправленных грузов', max_length=128, blank=True, null=True)
    number_of_goods_issued = models.CharField('Количество выданных грузов', max_length=128, blank=True, null=True)
    weight_of_goods_sent = models.CharField('Вес отправленных грузов', max_length=128, blank=True, null=True)
    volume_of_cargo_sent = models.CharField('Объем отправленных грузов', max_length=128, blank=True, null=True)
    number_of_calls = models.CharField('Количество звонков', max_length=128, blank=True, null=True)
    duration_of_calls = models.CharField('Длительность разговоров', max_length=128, blank=True, null=True)

    manager_id = models.ForeignKey('CustomUser', on_delete=models.PROTECT, blank=True, null=True)
    report_upload_date = models.DateTimeField(verbose_name='Дата загрузки отчета', blank=True, null=True)
    time_create = models.DateTimeField(auto_now_add=True)
    time_update = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Отчетность менеджера {self.manager_id} на дату {(self.report_upload_date + datetime.timedelta(hours=3))}"

    class Meta:
        verbose_name = 'Отчетность менеджеров'
        verbose_name_plural = 'Отчетность менеджеров'
        ordering = ['-report_upload_date']


class ManagerPlans(models.Model):
    manager_monthly_net_profit_plan = models.CharField('План по чистой прибыли в месяц', max_length=200, blank=True, null=True)
    month = models.IntegerField('Месяц', blank=True, null=True)
    year = models.IntegerField('Год', blank=True, null=True)
    manager_id = models.ForeignKey('CustomUser', on_delete=models.PROTECT, blank=True, null=True, related_name='plans')
    time_create = models.DateTimeField(auto_now_add=True, verbose_name='Дата создания')
    time_update = models.DateTimeField(auto_now=True, verbose_name='Дата обновления')

    def __str__(self):
        return f"План по чистой прибыли менеджера {self.manager_id} на {self.month}.{self.year} = {self.manager_monthly_net_profit_plan}"

    class Meta:
        verbose_name = 'План менеджера'
        verbose_name_plural = 'Планы менеджеров'
        ordering = ['-time_create']

def calculate_work_years(date_reg):
    if pd.isnull(date_reg):
        return None, None
    today = datetime.datetime.today()
    years = today.year - date_reg.year - ((today.month, today.day) < (date_reg.month, date_reg.day))
    return max(years, 1), date_reg.date()

class CallsFile(models.Model):
    CRM = [
        ('Битрикс24', 'Битрикс24'),
        ('amoCRM', 'acoCRM'),
        ('Росаккредитация', 'Росаккредитация'),
        ('Ozon', 'Ozon'),
    ]
    crm = models.CharField(max_length=50, choices=CRM, verbose_name='CRM')
    user = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, null=True, verbose_name='Пользователь')
    file = models.FileField(upload_to='files/calls/%Y/%m/%d/', verbose_name='Файл')
    uploaded_at = models.DateTimeField(auto_now_add=True, verbose_name='Дата загрузки')

    def __str__(self):
        return f"{self.file.name} ({self.uploaded_at})"

    class Meta:
        verbose_name = 'Загруженный файл Call'
        verbose_name_plural = 'Загруженные файлы Calls'

    def _parse_rosaccreditation(self, user):
        db_path = self.file.path
        conn = sqlite3.connect(db_path)
        df_company = pd.read_sql_query("SELECT * FROM company", conn)
        df_decl = pd.read_sql_query("SELECT id_company, date_registration FROM declaration", conn)

        # Преобразуем даты
        df_decl['date_registration'] = pd.to_datetime(df_decl['date_registration'], format="%d.%m.%Y", errors='coerce')

        # Оставим по одной записи на компанию (самую раннюю дату)
        df_decl = df_decl.sort_values('date_registration').drop_duplicates('id_company')

        # Соединяем по id_company
        df = df_company.merge(df_decl, on='id_company', how='left')
        conn.close()

        operators = list(CustomUser.objects.filter(role='Оператор'))
        current_operator_index = 0
        existing_phones = Calls.get_existing_phones()
        calls_to_create = []

        created_calls_count = 0
        duplicate_phone_count = 0
        total_rows = len(df)

        for _, row in df.iterrows():
            name_parts = [row.get('last_name_director'), row.get('name_director'), row.get('otch_director')]
            client_name = ' '.join(filter(lambda x: x and x != '-' and x != ' ', name_parts)).strip()

            client_phone = str(row.get('phone')).strip()
            if not client_name or not client_phone:
                continue

            if client_phone in existing_phones:
                duplicate_phone_count += 1
                continue

            operator = operators[current_operator_index] if operators else None
            current_operator_index = (current_operator_index + 1) % len(operators) if operators else 0

            company_type = row.get('type_company') or ''
            client_location = row.get('address') or ''
            raw_date = row.get('date_registration')
            work_years, date_registration = calculate_work_years(raw_date)

            call = Calls(
                client_name=client_name,
                client_phone=client_phone,
                status_call='Не обработано',
                date_call=timezone.now(),
                operator=operator,
                call_file=self,
                company_type=company_type,
                client_location=client_location,
                work_years=work_years,
                date_registration=date_registration
            )
            calls_to_create.append(call)
            existing_phones.add(client_phone)

        if calls_to_create:
            Calls.objects.bulk_create(calls_to_create)
            created_calls_count += len(calls_to_create)

        return {
            'created': created_calls_count,
            'duplicates': duplicate_phone_count,
            'total': total_rows
        }

    def parse_and_generate_calls(self, user):
        if self.crm == 'Росаккредитация':
            return self._parse_rosaccreditation(user)
        else:
            BATCH_SIZE = 10000
            excel_file = self.file
            df = pd.read_excel(excel_file)

            column_mapping = {
                'client_name': ['название лида', 'имя', 'фамилия', 'имя клиента', 'компания', 'название продавца'],
                'client_phone': ['телефон', 'телефоны', 'номер телефона', 'контактный номер', 'рабочий телефон', 'мобильные телефоны', 'городские телефоны'],
                'company_type': ['тип компании', 'организационно-правовая форма', 'форма собственности'],
                'seller_page': ['страница продавца', 'сайт', 'url', 'адрес сайта'],
                'work_years': ['работает с ', 'работает с ozon', 'лет с озон', 'опыт работы'],
                'date_registration': ['дата создания'],
                'client_location': ['город клиента', 'адрес продавца', 'юридический адрес']
            }

            normalized_columns = {key: [] for key in column_mapping}
            for col in df.columns:
                for key, aliases in column_mapping.items():
                    if find_best_matches(col, aliases):
                        normalized_columns[key].append(col)
                        break

            missing_columns = [key for key in ['client_name', 'client_phone'] if not normalized_columns[key]]
            if missing_columns:
                raise ValueError(f'Отсутствуют необходимые колонки: {", ".join(missing_columns)}.')

            operators = list(CustomUser.objects.filter(role='Оператор'))
            current_operator_index = 0
            existing_phones = Calls.get_existing_phones()
            calls_to_create = []

            total_rows = len(df)
            created_calls_count = 0
            duplicate_phone_count = 0

            for index, row in df.iterrows():
                if operators:
                    current_operator = operators[current_operator_index]
                    current_operator_index = (current_operator_index + 1) % len(operators)
                else:
                    current_operator = None

                call = Calls.create_from_row(row, normalized_columns, current_operator, self)

                # Альтернатива: вычисление work_years по дате создания, если нет значения
                if call and not call.work_years and normalized_columns.get('date_registration'):
                    raw_date = row[normalized_columns['date_registration'][0]]
                    if pd.notnull(raw_date):
                        try:
                            parsed_date = pd.to_datetime(raw_date, errors='coerce')
                            if not pd.isnull(parsed_date):
                                call.work_years, call.date_registration = calculate_work_years(parsed_date)
                        except Exception:
                            pass

                if call:
                    if call.client_phone in existing_phones:
                        duplicate_phone_count += 1
                        continue
                    calls_to_create.append(call)
                    existing_phones.add(call.client_phone)

                if len(calls_to_create) >= BATCH_SIZE:
                    Calls.objects.bulk_create(calls_to_create)
                    created_calls_count += len(calls_to_create)
                    calls_to_create = []

            if calls_to_create:
                Calls.objects.bulk_create(calls_to_create)
                created_calls_count += len(calls_to_create)

            return {
                'created': created_calls_count,
                'duplicates': duplicate_phone_count,
                'total': total_rows
            }

CRM_CHOICES = [
        ('Росаккредитация', 'Росаккредитация'),
        ('Колл-центр Альфа', 'Колл-центр Альфа'),
        ('Колл-центр Биг Дата', 'Колл-центр Биг Дата'),
        ('Колл-центр АЗ', 'Колл-центр АЗ'),
        ('Битрикс24', 'Битрикс24'),
        ('amoCRM', 'amoCRM'),
        ('Ozon', 'Ozon'),
        ('Наш сайт', 'Наш сайт'),
    ]

class Calls(models.Model):
    statuses_operator = [
        ('Не обработано', 'Не обработано'),
        ('Не дозвонились', 'Не дозвонились'),
        ('Не заинтересован', 'Не заинтересован'),
        ('Заинтересован', 'Заинтересован'),
        ('Перезвонить позже', 'Перезвонить позже'),
        ('Уже в работе', 'Уже в работе')
    ]
    statuses_manager = [
        ('Новая', 'Новая'),
        ('В работе', 'В работе'),
        ('Утверждена', 'Утверждена'),
        ('Отказ', 'Отказ')
    ]
    statuses_loyalty = [
        (1, 'Холодный'),
        (2, 'Теплый'),
        (3, 'Горячий'),
    ]


    operator = models.ForeignKey(CustomUser, verbose_name='Ответственный оператор', on_delete=models.SET_NULL, blank=True, null=True, related_name="operator_calls")
    date_call = models.DateTimeField(verbose_name='Дата звонка', blank=True, null=True)
    client_name = models.CharField(verbose_name='ФИО клиента', max_length=255, blank=True, null=True)
    client_phone = models.CharField(verbose_name='Контактный номер', max_length=550, unique=True)
    company_type = models.CharField(max_length=50, verbose_name='Тип компании', blank=True, null=True)
    seller_page = models.URLField(verbose_name='Страница продавца', blank=True, null=True)
    work_years = models.PositiveIntegerField(verbose_name='Сколько лет работает', blank=True, null=True)
    date_registration = models.DateField(verbose_name='Дата регистрации в CRM', blank=True, null=True)

    client_location = models.CharField(verbose_name='Город клиента', max_length=255, blank=True, null=True)
    description = models.TextField(verbose_name='Комментарий по звонку оператор', max_length=600, blank=True, null=True)
    status_call = models.CharField(default="Не обработано", choices=statuses_operator, verbose_name='Статус заявки', max_length=50)
    date_next_call = models.DateTimeField(verbose_name='Дата следующего звонка', blank=True, null=True)
    loyalty = models.IntegerField(choices=statuses_loyalty, verbose_name='Статус лояльности', blank=True, null=True)

    manager = models.ForeignKey(CustomUser, verbose_name='Ответственный менеджер', on_delete=models.SET_NULL, blank=True, null=True, related_name="manager_calls")
    date_to_manager = models.DateTimeField(verbose_name='Дата передачи менеджеру', blank=True, null=True)
    status_manager = models.CharField(default="Новая", choices=statuses_manager, verbose_name='Статус заявки менеджера', max_length=50)
    date_next_call_manager = models.DateTimeField(verbose_name='Дата следующего звонка менеджером', blank=True, null=True)
    description_manager = models.TextField(verbose_name='Комментарий по звонку менеджером', max_length=600, blank=True, null=True)

    call_file = models.ForeignKey(CallsFile, on_delete=models.SET_NULL, blank=True, null=True)

    crm = models.CharField(
        max_length=50,
        choices=CRM_CHOICES,
        verbose_name='Источник/CRM',
        blank=True,
        null=True, db_index=True
    )

    time_create = models.DateTimeField(auto_now_add=True)
    time_update = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Заявка на прозвон {self.client_name} {self.client_phone}"

    class Meta:
        verbose_name = 'Звонки'
        verbose_name_plural = 'Звонки'
        ordering = ['-time_create']

    @classmethod
    def filter_by_users(cls, selected_users=None, selected_operator_statuses=None, selected_manager_statuses=None):
        calls_query = cls.objects.all()

        if selected_users:
            calls_query = calls_query.filter(
                Q(manager__in=selected_users) | Q(operator__in=selected_users)
            )

        if selected_operator_statuses:
            calls_query = calls_query.filter(status_call__in=selected_operator_statuses)

        if selected_manager_statuses:
            calls_query = calls_query.filter(status_manager__in=selected_manager_statuses)

        return calls_query.select_related('operator', 'manager').order_by('pk')

    @classmethod
    def filter_by_status(cls, user, selected_operator_statuses=None, selected_manager_statuses=None, selected_managers=None, selected_crms=None):
        if user.role in ['Супер Администратор', 'РОП']:
            calls_query = cls.objects.select_related('operator', 'manager', 'call_file').order_by('pk').all()
        elif user.role == 'Менеджер':
            calls_query = cls.objects.filter(operator=user).select_related('operator', 'manager', 'call_file').order_by('pk').all()
        elif user.role == 'Оператор':
            calls_query = cls.objects.filter(Q(operator=user) | Q(operator__isnull=True)).select_related('operator', 'manager', 'call_file').order_by('pk').all()
        if selected_operator_statuses:
            calls_query = calls_query.filter(status_call__in=selected_operator_statuses)
        if selected_manager_statuses:
            calls_query = calls_query.filter(status_manager__in=selected_manager_statuses)
        if selected_managers:
            calls_query = calls_query.filter(operator__in=selected_managers)
        if selected_crms:
            # Фильтруем по Calls.crm ИЛИ по CallsFile.crm
            calls_query = calls_query.filter(
                Q(crm__in=selected_crms) | Q(call_file__crm__in=selected_crms)
            ).distinct()
        return calls_query

    @classmethod
    def all_calls_done(cls):
        return cls.objects.exclude(status_call="Не обработано").select_related('operator', 'manager').count()

    @classmethod
    def search(cls, query, queryset):
        return queryset.filter(
            Q(client_phone__iregex=query)
            |
            Q(client_name__iregex=query)
            |
            Q(client_location__iregex=query)
            |
            Q(description__iregex=query)
        )

    @classmethod
    def normalize_client_name(cls, row, columns):
        client_name_parts = []
        for col in columns:
            value = str(row[col]).strip() if pd.notnull(row[col]) else None
            if value:
                client_name_parts.append(value)
        return ' '.join(client_name_parts) if client_name_parts else None

    @classmethod
    def create_from_row(cls, row, columns, operator, call_file):
        client_name = cls.normalize_client_name(row, columns['client_name'])

        phones = []
        for phone_col in columns['client_phone']:
            raw_phone = row.get(phone_col)
            if pd.isnull(raw_phone):
                continue
            phone = str(raw_phone).strip()
            if phone:
                phones.append(phone)

        if not client_name or not phones:
            return None

        combined_phones = ', '.join(phones)

        company_type = None
        seller_page = None

        client_location = None
        if 'client_location' in columns and columns['client_location']:
            for col in columns['client_location']:
                val = row.get(col)
                if pd.notnull(val):
                    client_location = str(val).strip()
                    if client_location:
                        break

        if 'company_type' in columns and columns['company_type']:
            company_type = str(row[columns['company_type'][0]]).strip() if pd.notnull(row[columns['company_type'][0]]) else None

        if 'seller_page' in columns and columns['seller_page']:
            seller_page = str(row[columns['seller_page'][0]]).strip() if pd.notnull(row[columns['seller_page'][0]]) else None

        work_years = None
        if 'work_years' in columns and columns['work_years']:
            raw = str(row[columns['work_years'][0]]).lower().strip()
            match = re.search(r'(\d+)', raw)
            if match:
                years = int(match.group(1))
                # если упоминаются "дней", "день", "месяц" — считаем как 1 год
                if any(keyword in raw for keyword in ['дн', 'день', 'дней', 'месяц', 'месяцев', 'мес']):
                    work_years = 1
                else:
                    work_years = max(years, 1)
            else:
                work_years = None

        return cls(
            client_name=client_name,
            client_phone=combined_phones,
            client_location=client_location,
            company_type=company_type,
            seller_page=seller_page,
            work_years=work_years,
            status_call='Не обработано',
            date_call=timezone.now(),
            operator=operator,
            call_file=call_file,
        )

    @classmethod
    def get_new_calls(cls, operator):
        return cls.objects.filter(operator=operator, status_call='Не обработано').select_related('operator', 'manager').count()

    @classmethod
    def get_existing_phones(cls):
        return set(cls.objects.values_list('client_phone', flat=True))

    @staticmethod
    def clear_all():
        with transaction.atomic():
            Calls.objects.all().delete()

    def create_or_get_lead(self):
        """
        Создаёт новый Lead, если он не существует, или возвращает существующий.
        """
        if self.manager:
            try:
                # Проверяем, существует ли уже связанный Lead
                lead = self.leads  # Используем related_name="leads" из модели Leads
                # # Если Lead существует, обновляем его данные
                if lead.manager != self.manager:
                    lead.manager = self.manager
                    # lead.client_name = self.client_name
                    # lead.client_phone = self.client_phone
                    # lead.client_location = self.client_location
                    # lead.status_manager = 'Новая'
                    # lead.date_next_call_manager = self.date_next_call_manager
                    # lead.description_manager = self.description_manager
                    lead.time_new = self.date_to_manager
                    lead.save()  # Сохраняем изменения

                return lead  # Возвращаем обновлённый Lead
            except Leads.DoesNotExist:
                # Если Lead не существует, создаём новый
                lead = Leads.objects.create(
                    call=self,  # Связываем с текущим звонком
                    manager=self.manager,  # Переносим менеджера
                    client_name=self.client_name,  # Переносим имя клиента
                    client_phone=self.client_phone,  # Переносим телефон клиента
                    client_location=self.client_location,  # Переносим город клиента
                    loyalty=self.loyalty,  # Переносим город клиента

                    time_new=self.date_to_manager  # Переносим дату передачи менеджеру
                )
                return lead
        else:
            return None

    @classmethod
    def create_old_leads(cls):
        leads = cls.objects.filter(manager__isnull=False, leads__isnull=True).select_related('operator', 'manager', 'leads')
        for lead in leads:
            new_lead = Leads.objects.create(
                call=lead,
                manager=lead.manager,
                client_name=lead.client_name,
                client_phone=lead.client_phone,
                client_location=lead.client_location,
                status_manager=lead.status_manager,

                date_next_call_manager=lead.date_next_call_manager,
                description_manager=lead.description_manager,
                time_new=lead.date_to_manager,
            )
            if new_lead.status_manager == 'В работе':
                new_lead.time_in_work = lead.date_to_manager
            if new_lead.status_manager == 'Утверждена':
                new_lead.time_in_work = lead.date_to_manager
                new_lead.time_approve = lead.date_to_manager
            if new_lead.status_manager == 'Отказ':
                new_lead.time_in_work = lead.date_to_manager
                new_lead.time_no = lead.date_to_manager
            new_lead.save()
        return leads


class Leads(models.Model):
    statuses_manager = [
        ('Новая', 'Новая'),
        ('В работе', 'В работе'),
        ('Отложено', 'Отложено'),
        ('Утверждена', 'Утверждена'),
        ('Отказ', 'Отказ'),
        ('Не подходит под критерии', 'Не подходит под критерии')
    ]
    statuses_loyalty = [
        (1, 'Холодный'),
        (2, 'Теплый'),
        (3, 'Горячий'),
    ]
    call = models.OneToOneField(Calls, verbose_name='Звонок', on_delete=models.SET_NULL, blank=True, null=True, related_name="leads")
    manager = models.ForeignKey(CustomUser, verbose_name='Ответственный менеджер', on_delete=models.SET_NULL, blank=True, null=True, related_name="manager_leads")

    client_name = models.CharField(verbose_name='ФИО клиента', max_length=255, blank=True, null=True)
    client_phone = models.CharField(verbose_name='Контактный номер', max_length=50, unique=True)
    client_location = models.CharField(verbose_name='Город клиента', max_length=255, blank=True, null=True)
    loyalty = models.IntegerField(choices=statuses_loyalty, verbose_name='Статус лояльности', blank=True, null=True)

    status_manager = models.CharField(default="Новая", choices=statuses_manager, verbose_name='Статус заявки менеджера', max_length=50)
    date_next_call_manager = models.DateTimeField(verbose_name='Дата следующего звонка менеджером', blank=True, null=True)
    description_manager = models.TextField(verbose_name='Комментарий по звонку менеджером', max_length=600, blank=True, null=True)

    time_new = models.DateTimeField(verbose_name='Дата передачи менеджеру', blank=True, null=True)
    time_in_work = models.DateTimeField(verbose_name='Дата взятия В работу', blank=True, null=True)
    time_approve_no_other = models.DateTimeField(verbose_name='Дата Утверждения/Отказа/Другое', blank=True, null=True)

    time_create = models.DateTimeField(auto_now_add=True)
    time_update = models.DateTimeField(auto_now=True)

    history = HistoricalRecords()

    def __str__(self):
        return f"Лид {self.client_name} {self.client_phone}"

    class Meta:
        verbose_name = 'Лиды'
        verbose_name_plural = 'Лиды'
        ordering = ['-time_new']

    # def save(self, *args, **kwargs):
    #     super().save(*args, **kwargs)
    #     self.create_or_update_notifications()
    #
    # def create_or_update_notifications(self):
    #     """
    #     Создаёт или обновляет уведомления для текущего лида.
    #     """
    #     if self.status_manager in ['В работе', 'Отложено'] and self.date_next_call_manager:
    #         # Очистить старые уведомления
    #         self.notifications.all().delete()
    #
    #         # Первое уведомление: за 30 минут до звонка
    #         first_notification_time = self.date_next_call_manager - datetime.timedelta(minutes=30)
    #         TelegramNotification.objects.create(
    #             lead=self,
    #             manager=self.manager,
    #             notification_type='30_min_before',
    #             scheduled_time=first_notification_time
    #         )
    #
    #         # Второе уведомление: в 9:00 следующего дня, если дата звонка меньше полуночи
    #         if self.date_next_call_manager < localtime(now()).replace(hour=0, minute=0, second=0, microsecond=0):
    #             next_day_9am = localtime(now()).replace(hour=9, minute=0, second=0, microsecond=0) + datetime.timedelta(days=1)
    #             TelegramNotification.objects.create(
    #                 lead=self,
    #                 manager=self.manager,
    #                 notification_type='next_day_9am',
    #                 scheduled_time=next_day_9am
    #             )

    @staticmethod
    def get_status_change_dates_qs(target_statuses):
        """
        Возвращает QuerySet с лидами и их датами смены статусов.
        :param target_statuses: Список статусов, для которых нужно найти даты.
        :return: QuerySet с дополнительными аннотированными полями.
        """
        # Подзапрос для получения первой даты смены статуса
        subqueries = {}
        for status in target_statuses:
            subquery = Leads.history.filter(
                id=OuterRef('id'),  # Связываем с основной таблицей
                status_manager=status
            ).order_by('history_date').values('history_date')[:1]  # Берем первую запись
            subqueries[status] = Subquery(subquery)

        # Аннотируем основной QuerySet датами смены статусов
        leads_with_dates = Leads.objects.annotate(**subqueries)
        return leads_with_dates

    @staticmethod
    def delete_empty_manager():
        """
                Удаляет все лиды, у которых пустое значение менеджера.
        """
        with transaction.atomic():
            Leads.objects.filter(manager__isnull=True).delete()

    @classmethod
    def search(cls, query, queryset):
        return queryset.filter(
            Q(client_phone__iregex=query)
            |
            Q(client_name__iregex=query)
            |
            Q(client_location__iregex=query)
            |
            Q(description_manager__iregex=query)
        )

    @classmethod
    def filter_by_status(cls, user, selected_manager_statuses=None, selected_managers=None):
        if user.role in ['Супер Администратор', 'РОП']:
            leads_query = cls.objects.select_related('call', 'manager').order_by('pk').all()
        elif user.role == 'Менеджер':
            leads_query = cls.objects.filter(manager=user).select_related('call', 'manager').order_by('pk').all()
        if selected_manager_statuses:
            leads_query = leads_query.filter(status_manager__in=selected_manager_statuses)
        if selected_managers:
            leads_query = leads_query.filter(manager__in=selected_managers)

        return leads_query
