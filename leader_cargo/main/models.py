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
        ('Администратор', 'Администратор'),
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
    time_create = models.DateTimeField(auto_now_add=True, verbose_name='Дата создания')
    time_update = models.DateTimeField(auto_now=True, verbose_name='Дата изменения')
    status = models.BooleanField(default=True, choices=statuses, verbose_name='Статус')

    class Meta:
        verbose_name = 'Пользователи'
        verbose_name_plural = 'Пользователи'
        ordering = ['role', '-time_create']

    def get_absolute_url_client(self):
        return reverse('card_client', kwargs={'client_id': self.pk})

    def get_absolute_url_employee(self):
        return reverse('card_employees', kwargs={'employee_id': self.pk})

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
    tag = models.CharField('Тег заявки', max_length=50)
    status = models.CharField('Статус заявки', max_length=50)
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
# def user_directory_path(instance, filename):
#     # file will be uploaded to MEDIA_ROOT / user_<id>/<filename>
#     return 'photos/goods/user_{0}/{1}'.format(instance.user.id, filename)


class Goods(models.Model):
    name = models.CharField('Название товара', max_length=128, blank=False, null=True)
    photo_good = models.ImageField(verbose_name='Фото товара', upload_to='photos/goods/%Y/%m/%d/', blank=True, null=True)
    # photo_good = models.ImageField(verbose_name='Фото товара', upload_to=content_file_name)
    link_url = models.CharField('Ссылка на товар', max_length=200, blank=True, null=True)
    product_description = models.CharField('Описание товара', max_length=1024, blank=True, null=True)
    price_rmb = models.CharField(verbose_name='Цена товара в Китае в юанях', max_length=50, blank=True, null=True)
    quantity = models.CharField(verbose_name='Количество', max_length=50, blank=True, null=True)
    price_delivery = models.CharField(verbose_name='Стоимость доставки', max_length=50, blank=True, null=True)
    price_purchase = models.FloatField(verbose_name='Закупочная цена', blank=True, null=True)
    price_site = models.FloatField(verbose_name='Цена на сайте', blank=True, null=True)
    price_delivery_real = models.FloatField(verbose_name='Стоимость доставки реальная', blank=True, null=True)
    appeal_id = models.ForeignKey('Appeals', on_delete=models.PROTECT, blank=True, null=True)
    time_create = models.DateTimeField(auto_now_add=True)
    time_update = models.DateTimeField(auto_now=True)
    status = models.BooleanField(default=True, blank=True, null=True)

    def __str__(self):
        return f"{self.name}"

    class Meta:
        verbose_name = 'Список товаров'
        verbose_name_plural = 'Список товаров'

    def get_itog(self):
        summ = 0
        if self.price_rmb and self.quantity:
            summ = summ + float(self.price_rmb.replace(' ', ''))*float(self.quantity.replace(' ', ''))
        if self.price_delivery:
            summ = summ + float(self.price_delivery.replace(' ', ''))
        return summ
