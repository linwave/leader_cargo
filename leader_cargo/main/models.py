import datetime

from django.contrib.auth.models import AbstractUser
from django.db import models
from django.urls import reverse


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
        ordering = ['-status', 'town', 'role', '-time_create']

    def __str__(self):
        return f"{self.last_name} {self.first_name} - {self.phone}"

    def get_absolute_url_client(self):
        return reverse('card_client', kwargs={'client_id': self.pk})

    def get_absolute_url_employee(self):
        return reverse('card_employees', kwargs={'employee_id': self.pk})

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
    yuan = models.FloatField(verbose_name='Курс ¥', blank=False, null=True)
    dollar = models.FloatField(verbose_name='Курс $', blank=False, null=True)
    time_create = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.time_create} {self.yuan} {self.dollar}"

    class Meta:
        verbose_name = 'Курсы валют'
        verbose_name_plural = 'Курсы валют'


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

    def get_absolute_url(self):
        return reverse('card_appeal', kwargs={'appeal_id': self.pk})

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