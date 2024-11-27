import datetime
from django.utils.timezone import make_aware
from django.db import models

from main.models import CustomUser
from django.urls import reverse
import os
import uuid


def get_file_path(instance, filename):
    ext = filename.split('.')[-1]
    filename = "%s.%s" % (uuid.uuid4(), ext)
    return os.path.join(instance.directory_string_var, filename)


class CargoFiles(models.Model):
    carriers = [
        ('Ян', 'Ян'),
        # ('Ян (новый)', 'Ян (новый)'),
        ('Ян (полная машина)', 'Ян (полная машина)'),
        ('Валька', 'Валька'),
        ('Мурад', 'Мурад'),
        ('Гелик', 'Гелик')
    ]
    name_carrier = models.CharField(max_length=50, choices=carriers, verbose_name='Перевозчик')
    file_path = models.FileField(verbose_name='Файлы перевозчиков', upload_to='files/cargo/%Y/%m/%d/', blank=False, null=False)
    time_create = models.DateTimeField(auto_now_add=True)
    time_update = models.DateTimeField(auto_now=True)
    status = models.BooleanField(default=True, blank=True, null=True)

    def __str__(self):
        return f"{self.name_carrier} {self.file_path}"

    class Meta:
        verbose_name = 'Файлы грузов'
        verbose_name_plural = 'Файлы грузов'


class CargoArticle(models.Model):
    statuses = [
        ('В пути', 'В пути'),
        ('Прибыл в РФ', 'Прибыл в РФ')
    ]
    paid_by_the_client_statuses = [
        ('Оплачено полностью', 'Оплачено полностью'),
        ('Оплачено частично', 'Оплачено частично'),
        ('Не оплачено', 'Не оплачено'),
    ]
    payment_to_the_carrier_statuses = [
        ('Оплачено', 'Оплачено'),
        ('Не оплачено', 'Не оплачено'),
    ]
    carriers = [
        ('Ян', 'Ян'),
        ('Валька', 'Валька'),
        ('Мурад', 'Мурад'),
        ('Гелик', 'Гелик'),
        ('Склад №5', 'Склад №5')
    ]
    path_formats = [
        ('Быстрое авто', 'Быстрое авто'),
        ('Обычное авто', 'Обычное авто'),
        ('Уссурийск', 'Уссурийск'),
        ('ЖД', 'ЖД'),
        ('Авиа', 'Авиа')
    ]
    managers = CustomUser.objects.filter(role__in=['Менеджер', 'РОП'], status=True).order_by('last_name')
    managers_choices = []
    if managers:
        for manager in managers:
            managers_choices.append((f'{manager.pk}', f'{manager.last_name} {manager.first_name}'))

    article = models.CharField(max_length=50, verbose_name='Артикул')
    responsible_manager = models.CharField(max_length=100, verbose_name='Ответственный менеджер', choices=managers_choices, blank=True, null=True)
    carrier = models.CharField(max_length=100, verbose_name='Перевозчик', choices=carriers, blank=True, null=True)
    path_format = models.CharField(max_length=100, verbose_name='Формат пути', choices=path_formats, blank=True, null=True)
    name_goods = models.CharField(max_length=50, verbose_name='Наименование товара', blank=True, null=True)
    number_of_seats = models.CharField(max_length=50, verbose_name='Количество мест')
    weight = models.CharField(max_length=50, verbose_name='Вес, кг')
    volume = models.CharField(max_length=50, verbose_name='Объем')
    transportation_tariff = models.CharField(max_length=50, verbose_name='Тариф перевозки')
    transportation_tariff_for_clients = models.CharField(max_length=50, verbose_name='Тариф перевозки для клиента', blank=True, null=True)
    cost_goods = models.CharField(max_length=50, verbose_name='Стоимость товара', blank=True, null=True)
    insurance_cost = models.CharField(max_length=50, verbose_name='Стоимость страховки', blank=True, null=True)
    packaging_cost = models.CharField(max_length=50, verbose_name='Стоимость упаковки', blank=True, null=True)
    time_from_china = models.DateTimeField(verbose_name='Дата отправки с Китайского склада', blank=True, null=True)
    total_cost = models.CharField(max_length=50, verbose_name='Итоговая стоимость перевозки', blank=True, null=True)
    address_transportation_cost = models.CharField(max_length=50, verbose_name='Адресная доставка', blank=True, null=True)

    prr = models.CharField(max_length=50, verbose_name='ПРР', blank=True, null=True)
    tat_cost = models.CharField(max_length=50, verbose_name='Оплата ТАТ', blank=True, null=True)
    paid_by_the_client_status = models.CharField(max_length=50, default='Не оплачено',
                                                 choices=paid_by_the_client_statuses, verbose_name='Оплачено клиентом', blank=True, null=True)
    time_paid_by_the_client_status = models.DateTimeField(verbose_name='Дата полной оплаты клиентом', blank=True, null=True)
    payment_to_the_carrier_status = models.CharField(max_length=50, default='Не оплачено',
                                                     choices=payment_to_the_carrier_statuses, verbose_name='Оплата перевозчику', blank=True, null=True)
    time_cargo_arrival_to_RF = models.DateTimeField(verbose_name='Дата прибытия груза в РФ', blank=True, null=True)
    time_cargo_release = models.DateTimeField(verbose_name='Дата выдачи груза', blank=True, null=True)

    cargo_id = models.ForeignKey('CargoFiles', on_delete=models.PROTECT, blank=True, null=True)

    transportation_tariff_with_factor = models.FloatField(verbose_name='Тариф перевозки с коэффициентом', blank=True, null=True)
    transportation_tariff_with_factor_multi = models.CharField(max_length=255, verbose_name='Тариф перевозки с коэффициентом комбинированная', blank=True, null=True)
    total_cost_with_factor = models.FloatField(verbose_name='Итоговая стоимость перевозки с коэффициентом', blank=True, null=True)

    time_create = models.DateTimeField(auto_now_add=True)
    time_update = models.DateTimeField(auto_now=True)
    status = models.CharField(max_length=50, default='В пути', choices=statuses, verbose_name='Статус', blank=True, null=True)

    def __str__(self):
        return f"{self.article} {self.status}"

    class Meta:
        verbose_name = 'Артикула'
        verbose_name_plural = 'Артикула'
        ordering = ['-time_from_china']

    def get_FI_responsible_manager(self):
        try:
            manager = CustomUser.objects.get(pk=int(self.responsible_manager), status=True)
            return f'{manager.last_name} {manager.first_name}'
        except TypeError:
            return None
        except ValueError:
            return None

    def get_short_name_transportation_tariff(self):
        if self.transportation_tariff_with_factor_multi:
            return self.transportation_tariff_with_factor_multi
        if self.transportation_tariff_with_factor:
            return round(self.transportation_tariff_with_factor, 2)
        return self.transportation_tariff.replace('+', ' +')

    def get_short_name_total_cost(self):
        if self.total_cost_with_factor:
            return self.total_cost_with_factor
        return self.total_cost

    def get_number_of_days_on_the_way(self):
        if self.time_cargo_arrival_to_RF and self.time_from_china:
            return (self.time_cargo_arrival_to_RF - self.time_from_china).days
        else:
            return ''

    def get_number_of_days_without_payment(self):
        if self.time_paid_by_the_client_status and self.time_cargo_release:
            day = (self.time_paid_by_the_client_status - self.time_cargo_release).days
            if day < 0:
                return 0
            return day
        elif self.time_cargo_release:
            return (make_aware(datetime.datetime.now()) - self.time_cargo_release).days
        else:
            return ''

    def update_status_article(self):
        if self.status == 'Прибыл в РФ':
            self.status = 'В пути'
        elif self.status == 'В пути':
            self.status = 'Прибыл в РФ'
        self.save()


class PaymentDocumentsForArticles(models.Model):
    article = models.ForeignKey(CargoArticle, verbose_name='Артикул', on_delete=models.CASCADE, related_name='file_payment_by_client')
    name = models.CharField(verbose_name='Название файла', max_length=250, blank=True, null=True)
    file_path = models.FileField(verbose_name='Платежки', upload_to='files/logistic/client_payments/%Y/%m/%d/', blank=True, null=True)
    balance = models.FloatField(verbose_name='Деньги в платежки', blank=True, null=True)

    time_create = models.DateTimeField(auto_now_add=True)
    time_update = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Платежные документы - {self.article}"

    class Meta:
        verbose_name = 'Платежные документы'
        verbose_name_plural = 'Платежные документы'


class RoadsList(models.Model):
    name = models.CharField(max_length=100, verbose_name='Название дороги')
    activity = models.BooleanField(verbose_name='Статус активности дороги', default=True, blank=True, null=True)
    status = models.BooleanField(verbose_name='Статус', default=True)
    time_create = models.DateTimeField(auto_now_add=True)
    time_update = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.name}"

    class Meta:
        verbose_name = 'Список дорог'
        verbose_name_plural = 'Дороги'

    def all_parameters(self):
        return self.carriersroadparameters_set.all()


class CarriersList(models.Model):
    name = models.CharField(max_length=100, verbose_name='Название перевозчика')
    roads = models.ManyToManyField(RoadsList, through="CarriersRoadParameters")
    activity = models.BooleanField(verbose_name='Статус активности перевозчика', default=True, blank=True, null=True)

    status = models.BooleanField(verbose_name='Статус', default=True)
    time_create = models.DateTimeField(auto_now_add=True)
    time_update = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Перевозчик - {self.name}"

    class Meta:
        verbose_name = 'Список перевозчиков'
        verbose_name_plural = 'Перевозчики'

    def all_roads(self):
        return self.roads.all()


class CarriersRoadParameters(models.Model):
    carrier = models.ForeignKey(CarriersList, verbose_name='Перевозчик', on_delete=models.CASCADE)
    road = models.ForeignKey(RoadsList, verbose_name='Дорога', on_delete=models.CASCADE)
    min_transportation_time = models.IntegerField(verbose_name='Минимальный срок доставки', blank=True, null=True)
    max_transportation_time = models.IntegerField(verbose_name='Максимальный срок доставки', blank=True, null=True)


class PriceListsOfCarriers(models.Model):
    carrier_and_road = models.ForeignKey(CarriersRoadParameters, verbose_name='Перевозчик и дорога', on_delete=models.SET_NULL, null=True, related_name='density')
    min_density = models.IntegerField(verbose_name='Минимальная плотность', blank=True, null=True)
    max_density = models.IntegerField(verbose_name='Максимальная плотность', blank=True, null=True)
    price = models.IntegerField(verbose_name='Цена', blank=True, null=True)

    time_create = models.DateTimeField(auto_now_add=True)
    time_update = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.carrier_and_road} {self.min_density}-{self.max_density}"

    class Meta:
        verbose_name = 'Прайс листы перевозчиков'
        verbose_name_plural = 'Прайс листы перевозчиков'
        ordering = ['-min_density']


class RequestsForLogisticsCalculations(models.Model):
    statuses = [
        ('Черновик', 'Черновик'),
        ('Новый', 'Новый'),
        ('В работе', 'В работе'),
        ('На просчете', 'На просчете'),
        ('Частично обработано', 'Частично обработано'),
        ('Обработано', 'Обработано'),
        ('Запрос снижения тарифа', 'Запрос снижения тарифа'),
        ('Снижение невозможно', 'Снижение невозможно'),
        ('Перевозчик утвержден', 'Перевозчик утвержден'),
        ('Отклонено', 'Отклонено'),
        ('Запрос на изменение', 'Запрос на изменение'),
        ('Закрыт', 'Закрыт')
    ]
    name = models.CharField(max_length=50, verbose_name='Название запроса на просчет')
    initiator = models.ForeignKey(CustomUser, on_delete=models.PROTECT, verbose_name='Инициатор', related_name='initiator')
    logist = models.ForeignKey(CustomUser, on_delete=models.PROTECT, verbose_name='Логист', related_name='logist', blank=True, null=True)
    status = models.CharField(max_length=50, choices=statuses, verbose_name='Статус', blank=True, null=True)

    bid = models.CharField(max_length=50, verbose_name='Окончательная ставка', blank=True, null=True)
    reason_for_close = models.CharField(max_length=100, verbose_name='Причина закрытия', blank=True, null=True)
    carrier = models.ForeignKey(CarriersList, on_delete=models.PROTECT, verbose_name='Перевозчик', blank=True, null=True)
    roads = models.ManyToManyField(RoadsList)

    comments_initiator = models.CharField(max_length=250, verbose_name='Комментарии от инициатора', blank=True, null=True)
    comments_logist = models.CharField(max_length=250, verbose_name='Комментарии от логиста', blank=True, null=True)
    notification = models.BooleanField(verbose_name='Уведомление по заявке', default=False)

    file_path_request = models.FileField(verbose_name='Excel файл товаров по запросу',
                                         upload_to='files/logistic/requests/%Y/%m/%d/', blank=True, null=True)

    time_new = models.DateTimeField(verbose_name='Дата статуса Новый', blank=True, null=True)
    time_in_work = models.DateTimeField(verbose_name='Дата статуса В работе', blank=True, null=True)
    time_in_partially_work = models.DateTimeField(verbose_name='Дата статуса Частично обработано', blank=True, null=True)
    time_completed = models.DateTimeField(verbose_name='Дата статуса Отработано', blank=True, null=True)
    time_to_close_yes = models.DateTimeField(verbose_name='Дата статуса Перевозчик утвержден', blank=True, null=True)
    time_to_close_no = models.DateTimeField(verbose_name='Дата статуса Отклонено', blank=True, null=True)

    time_create = models.DateTimeField(auto_now_add=True)
    time_update = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.name}"

    class Meta:
        verbose_name = 'Запросы ставок'
        verbose_name_plural = 'Запросы ставок'
        ordering = ['-time_update']

    def get_absolute_url_request(self):
        return reverse('analytics:edit_logistic_requests', kwargs={'request_id': self.pk})


class RequestsForLogisticFiles(models.Model):
    directory_string_var = f'files/logistic/requests/{datetime.datetime.now().strftime("%Y/%m/%d/")}'
    request = models.ForeignKey(RequestsForLogisticsCalculations, on_delete=models.CASCADE)
    name = models.CharField(max_length=100, verbose_name='Название файла', blank=True, null=True)
    file_path_request = models.FileField(verbose_name='Файл по запросу',
                                         upload_to=get_file_path, blank=True, null=True)

    time_create = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Файл по запросу {self.request}"

    class Meta:
        verbose_name = 'Файлы по запросу логисту'
        verbose_name_plural = 'Файлы по запросу логисту'


class RequestsForLogisticsGoods(models.Model):
    directory_string_var = f'photos/logistic/goods/{datetime.datetime.now().strftime("%Y/%m/%d/")}'

    request = models.ForeignKey(RequestsForLogisticsCalculations, on_delete=models.CASCADE, related_name='goods')
    photo_path_logistic_goods = models.ImageField(verbose_name='Фото товара', upload_to=get_file_path, blank=True, null=True)
    description = models.CharField(max_length=255, verbose_name='Описание товара', blank=True, null=True)
    material = models.CharField(max_length=255, verbose_name='Материал', blank=True, null=True)
    number_of_packages = models.CharField(max_length=50, verbose_name='Количество упаковок/мест', blank=True, null=True)
    quantity_in_each_package = models.CharField(max_length=50, verbose_name='Количество в каждой упаковке (шт)', blank=True, null=True)
    size_of_packaging = models.CharField(max_length=50, verbose_name='Объём/размер упаковки (м3)', blank=True, null=True)
    gross_weight_of_packaging = models.CharField(max_length=50, verbose_name='Вес брутто упаковки (кг)', blank=True, null=True)
    total_volume = models.CharField(max_length=50, verbose_name='Общий объём (м3)', blank=True, null=True)
    total_gross_weight = models.CharField(max_length=50, verbose_name='Общий вес брутто (кг)', blank=True, null=True)
    total_quantity = models.CharField(max_length=50, verbose_name='Общее кол-во (шт)', blank=True, null=True)
    trademark = models.CharField(max_length=50, verbose_name='Торговая марка', blank=True, null=True)

    bid = models.CharField(max_length=50, verbose_name='Ставка товара', blank=True, null=True)

    time_create = models.DateTimeField(auto_now_add=True)
    time_update = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Товар {self.pk} запроса {self.request.name}"

    class Meta:
        verbose_name = 'Товары на запрос в логистику'
        verbose_name_plural = 'Товары на запрос в логистику'


class RequestsForLogisticsRate(models.Model):
    # request = models.ForeignKey(RequestsForLogisticsCalculations, on_delete=models.CASCADE, related_name='rate')
    good = models.ForeignKey(RequestsForLogisticsGoods, on_delete=models.CASCADE, related_name='rate')
    road = models.ForeignKey(RoadsList, on_delete=models.CASCADE, verbose_name='Название дороги')
    carrier = models.ForeignKey(CarriersList, on_delete=models.CASCADE, verbose_name='Название перевозчика')

    bid = models.CharField(max_length=50, verbose_name='Ставка', blank=True, null=True)
    active = models.BooleanField(default=False, verbose_name='Выбранная ставка', blank=True, null=True)

    time_create = models.DateTimeField(auto_now_add=True)
    time_update = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Ставка {self.bid} товара {self.good} дороги {self.road} перевозчика {self.carrier}"

    class Meta:
        verbose_name = 'Ставки на запрос в логистику'
        verbose_name_plural = 'Ставки на запрос в логистику'
