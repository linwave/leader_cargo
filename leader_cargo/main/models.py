import datetime
import logging

import pandas as pd
from django.contrib.auth.models import AbstractUser
from django.db import models, transaction
from django.urls import reverse
from django.utils import timezone

logger = logging.getLogger(__name__)

class CustomUser(AbstractUser):
    towns = [
        ('Москва', 'Москва'),
        ('Краснодар', 'Краснодар'),
    ]
    roles = [
        ('Супер Администратор', 'Супер Администратор'),
        ('РОП', 'РОП'),
        ('Администратор', 'Администратор'),
        ('Логист', 'Логист'),
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

    def get_absolute_url_client(self):
        return reverse('main:card_client', kwargs={'client_id': self.pk})

    def get_absolute_url_employee(self):
        return reverse('main:card_employees', kwargs={'employee_id': self.pk})

    def get_net_profit_to_the_company(self):
        for reports in self.managersreports_set.all():
            return reports

    def get_FI(self):
        return f'{self.last_name} {self.first_name}'

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
# class Clients(models.Model):
#     phone = models.CharField('Телефон', max_length=50, unique=True)
#     name = models.CharField('ФИО', max_length=50)
#     description = models.CharField('Описание', max_length=150)
#     manager = models.ForeignKey('Employees', on_delete=models.PROTECT)
#     password = models.CharField('Пароль', max_length=50)
#     time_create = models.DateTimeField(auto_now_add=True)
#     time_update = models.DateTimeField(auto_now=True)
#     status = models.BooleanField(default=True)
#
#     def __str__(self):
#         return f"{self.phone} {self.name}"
#
#     class Meta:
#         verbose_name = 'Список клиентов'
#         verbose_name_plural = 'Список клиентов'
#
#     def get_absolute_url(self):
#         return reverse('card_client', kwargs={'client_id': self.pk})


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
            result = result + float(self.price_rmb.replace(' ', '').replace(',', '.'))*float(self.quantity.replace(' ', '').replace(',', '.'))
        if self.price_delivery:
            result = result + float(self.price_delivery.replace(' ', '').replace(',', '.'))
        return result

    def get_result_self_yuan(self):
        result = 0
        if self.price_purchase and self.quantity:
            result = result + float(self.price_purchase.replace(' ', '').replace(',', '.'))*float(self.quantity.replace(' ', '').replace(',', '.'))
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
        return f"Отчетность менеджера {self.manager_id} на дату {(self.report_upload_date+datetime.timedelta(hours=3))}"

    class Meta:
        verbose_name = 'Отчетность менеджеров'
        verbose_name_plural = 'Отчетность менеджеров'
        ordering = ['-report_upload_date']


class ManagerPlans(models.Model):
    manager_monthly_net_profit_plan = models.CharField('План по чистой прибыли в месяц', max_length=200, blank=True, null=True)
    month = models.IntegerField('Месяц', blank=True, null=True)
    year = models.IntegerField('Год', blank=True, null=True)
    manager_id = models.ForeignKey('CustomUser', on_delete=models.PROTECT, blank=True, null=True)
    time_create = models.DateTimeField(auto_now_add=True, verbose_name='Дата создания')
    time_update = models.DateTimeField(auto_now=True, verbose_name='Дата обновления')

    def __str__(self):
        return f"План по чистой прибыли менеджера {self.manager_id} на {self.month}.{self.year} = {self.manager_monthly_net_profit_plan}"

    class Meta:
        verbose_name = 'План менеджера'
        verbose_name_plural = 'Планы менеджеров'
        ordering = ['-time_create']


class CallsFile(models.Model):
    CRM = [
            ('Битрикс24', 'Битрикс24'),
            ('amoCRM', 'acoCRM'),
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


class Calls(models.Model):
    statuses_operator = [
        ('Не обработано', 'Не обработано'),
        ('Не дозвонились', 'Не дозвонились'),
        ('Не заинтересован', 'Не заинтересован'),
        ('Заинтересован', 'Заинтересован'),
        ('Перезвонить позже', 'Перезвонить позже')
    ]
    statuses_manager = [
        ('Новая', 'Новая'),
        ('В работе', 'В работе'),
        ('Утверждена', 'Утверждена'),
        ('Отказ', 'Отказ')
    ]
    operator = models.ForeignKey(CustomUser, verbose_name='Ответственный оператор', on_delete=models.SET_NULL, blank=True, null=True, related_name="operator_calls")
    date_call = models.DateTimeField(verbose_name='Дата звонка', blank=True, null=True)
    client_name = models.CharField(verbose_name='ФИО клиента', max_length=255, blank=True, null=True)
    client_phone = models.CharField(verbose_name='Контактный номер', max_length=50, unique=True)
    client_location = models.CharField(verbose_name='Город клиента', max_length=50, blank=True, null=True)
    description = models.TextField(verbose_name='Комментарий по звонку оператор', max_length=600, blank=True, null=True)
    status_call = models.CharField(default="Не обработано", choices=statuses_operator, verbose_name='Статус заявки', max_length=50)
    date_next_call = models.DateTimeField(verbose_name='Дата следующего звонка', blank=True, null=True)

    manager = models.ForeignKey(CustomUser, verbose_name='Ответственный менеджер', on_delete=models.SET_NULL, blank=True, null=True, related_name="manager_calls")
    date_to_manager = models.DateTimeField(verbose_name='Дата передачи менеджеру', blank=True, null=True)
    status_manager = models.CharField(default="Новая", choices=statuses_manager, verbose_name='Статус заявки менеджера', max_length=50)
    date_next_call_manager = models.DateTimeField(verbose_name='Дата следующего звонка менеджером', blank=True, null=True)
    description_manager = models.TextField(verbose_name='Комментарий по звонку менеджером', max_length=600, blank=True, null=True)

    call_file = models.ForeignKey(CallsFile, on_delete=models.SET_NULL, blank=True, null=True)

    time_create = models.DateTimeField(auto_now_add=True)
    time_update = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Заявка на прозвон {self.client_name} {self.client_phone}"

    class Meta:
        verbose_name = 'Звонки'
        verbose_name_plural = 'Звонки'
        ordering = ['-time_create']

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
        client_phone = str(row[columns['client_phone'][0]]).strip() if pd.notnull(row[columns['client_phone'][0]]) else None

        if not client_name or not client_phone:
            # logger.warning(f'Пропущена строка: client_name={client_name}, client_phone={client_phone}')
            return None

        return cls(
            client_name=client_name,
            client_phone=client_phone,
            status_call='Не обработано',
            date_call=timezone.now(),
            operator=operator,
            call_file=call_file,
        )

    @classmethod
    def get_existing_phones(cls):
        return set(cls.objects.values_list('client_phone', flat=True))
    @staticmethod
    def clear_all():
        with transaction.atomic():
            Calls.objects.all().delete()

# class CallsFiles(models.Model):
#     CRM = [
#         ('Битрикс24', 'Битрикс24'),
#         ('amoCRM', 'acoCRM'),
#     ]
#     name_crm = models.CharField(max_length=50, choices=carriers, verbose_name='Перевозчик')
#     file_path = models.FileField(verbose_name='Файл CRM', upload_to='files/cargo/%Y/%m/%d/', blank=False, null=False)
#     time_create = models.DateTimeField(auto_now_add=True)
#     time_update = models.DateTimeField(auto_now=True)
#     status = models.BooleanField(default=True, blank=True, null=True)
#
#     def __str__(self):
#         return f"{self.name_carrier} {self.file_path}"
#
#     class Meta:
#         verbose_name = 'Файлы грузов'
#         verbose_name_plural = 'Файлы грузов'


