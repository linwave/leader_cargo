from django.db import models

from main.models import CustomUser


class CargoFiles(models.Model):
    carriers = [
        ('Ян', 'Ян'),
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
        ('Гелик', 'Гелик')
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
    payment_to_the_carrier_status = models.CharField(max_length=50, default='Не оплачено',
                                                     choices=payment_to_the_carrier_statuses, verbose_name='Оплата перевозчику', blank=True, null=True)
    time_cargo_arrival_to_RF = models.DateTimeField(verbose_name='Дата прибытия груза в РФ', blank=True, null=True)
    time_cargo_release = models.DateTimeField(verbose_name='Дата выдачи груза', blank=True, null=True)

    cargo_id = models.ForeignKey('CargoFiles', on_delete=models.PROTECT)

    transportation_tariff_with_factor = models.IntegerField(verbose_name='Тариф перевозки с коэффициентом', blank=True, null=True)
    total_cost_with_factor = models.IntegerField(verbose_name='Итоговая стоимость перевозки с коэффициентом', blank=True, null=True)

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
        return self.transportation_tariff.replace('+', ' +')

    def get_number_of_days_on_the_way(self):
        if self.time_cargo_arrival_to_RF and self.time_from_china:
            return (self.time_cargo_arrival_to_RF - self.time_from_china).days
        else:
            return ''

    def update_status_article(self):
        if self.status == 'Прибыл в РФ':
            self.status = 'В пути'
        elif self.status == 'В пути':
            self.status = 'Прибыл в РФ'
        self.save()


class PriceListsOfCarriers(models.Model):
    carriers = [
        ('Ян', 'Ян'),
        ('Валька', 'Валька'),
        ('Мурад', 'Мурад'),
        ('Гелик', 'Гелик')
    ]
    types_of_transportation = [
        ('Авто', 'Авто'),
        ('ЖД', 'ЖД'),
    ]
    types_of_product = [
        ('ТНП', 'ТНП'),
        ('Хозтовары', 'Хозтовары'),
        ('Одежда', 'Одежда'),
    ]
    carrier = models.CharField(max_length=50, choices=carriers, verbose_name='Перевозчик')
    type_of_transportation = models.CharField(max_length=50, choices=types_of_transportation, verbose_name='Тип перевозки')
    type_of_product = models.CharField(max_length=50, choices=types_of_product, verbose_name='Вид товара')
    min_transportation_time = models.IntegerField(verbose_name='Минимальный срок перевозки')
    max_transportation_time = models.IntegerField(verbose_name='Максимальный срок перевозки')
    min_density = models.IntegerField(verbose_name='Минимальная плотность')
    max_density = models.IntegerField(verbose_name='Максимальная плотность')

    time_create = models.DateTimeField(auto_now_add=True)
    time_update = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.carrier} {self.type_of_transportation} {self.type_of_product} {self.min_transportation_time}-{self.max_transportation_time}"

    class Meta:
        verbose_name = 'Прайс листы перевозчиков'
        verbose_name_plural = 'Прайс листы перевозчиков'


class RequestsForLogisticsCalculations(models.Model):
    statuses = [
        ('Черновик', 'Черновик'),
        ('Новый', 'Новый'),
        ('В работе', 'В работе'),
        ('Частично обработано', 'Частично обработано'),
        ('Обработано', 'Обработано'),
        ('Запрос снижения тарифа', 'Запрос снижения тарифа'),
        ('Снижение невозможно', 'Снижение невозможно'),
        ('Перевозчик утвержден', 'Перевозчик утвержден'),
        ('Отклонено', 'Отклонено')
    ]
    name = models.CharField(max_length=50, verbose_name='Название запроса')
    manager = models.ForeignKey(CustomUser, on_delete=models.PROTECT)
    status = models.CharField(max_length=50, verbose_name='Статус', blank=True, null=True)
    carriers = models.CharField(max_length=50, verbose_name='Перевозчики', blank=True, null=True)
    bid = models.CharField(max_length=50, verbose_name='Окончательная ставка', blank=True, null=True)
    # file_path_requests = models.FileField(verbose_name='Файл запроса', upload_to='files/logistic/requests/%Y/%m/%d/', blank=True, null=True)
    time_new = models.DateTimeField(verbose_name='Дата статуса Новый', blank=True, null=True)
    time_in_work = models.DateTimeField(verbose_name='Дата статуса В работе', blank=True, null=True)
    time_to_close_yes = models.DateTimeField(verbose_name='Дата статуса Перевозчик утвержден', blank=True, null=True)
    time_to_close_no = models.DateTimeField(verbose_name='Дата статуса Отклонено', blank=True, null=True)

    time_create = models.DateTimeField(auto_now_add=True)
    time_update = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.name}"

    class Meta:
        verbose_name = 'Запросы на логистику'
        verbose_name_plural = 'Запросы на логистику'
        ordering = ['-time_update']


class RequestsForLogisticsGoods(models.Model):
    request = models.ForeignKey(RequestsForLogisticsCalculations, on_delete=models.PROTECT)
    photo_path_logistic_goods = models.ImageField(verbose_name='Фото товара', upload_to='photo/logistic/goods/%Y/%m/%d/', blank=True, null=True)
    description = models.CharField(max_length=50, verbose_name='Описание товара', blank=True, null=True)
    material = models.CharField(max_length=50, verbose_name='Материал', blank=True, null=True)
    number_of_packages = models.CharField(max_length=50, verbose_name='Количество упаковок/мест', blank=True, null=True)
    quantity_in_each_package = models.CharField(max_length=50, verbose_name='Количество в каждой упаковке (шт)', blank=True, null=True)
    size_of_packaging = models.CharField(max_length=50, verbose_name='Объём/размер упаковки (м3)', blank=True, null=True)
    gross_weight_of_packaging = models.CharField(max_length=50, verbose_name='Вес брутто упаковки (кг)', blank=True, null=True)
    total_volume = models.CharField(max_length=50, verbose_name='Общий объём (м3)', blank=True, null=True)
    total_gross_weight = models.CharField(max_length=50, verbose_name='Общий вес брутто (кг)', blank=True, null=True)
    total_quantity = models.CharField(max_length=50, verbose_name='Общее кол-во (шт)', blank=True, null=True)
    trademark = models.CharField(max_length=50, verbose_name='Торговая марка', blank=True, null=True)

    time_create = models.DateTimeField(auto_now_add=True)
    time_update = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Товар {self.pk} запроса {self.request}"

    class Meta:
        verbose_name = 'Товары на запрос в логистику'
        verbose_name_plural = 'Товары на запрос в логистику'


class RequestsForLogisticsRate(models.Model):
    carriers = [
        ('Ян', 'Ян'),
        ('Валька', 'Валька'),
        ('Мурад', 'Мурад'),
        ('Гелик', 'Гелик')
    ]
    request = models.ForeignKey(RequestsForLogisticsCalculations, on_delete=models.PROTECT)
    road_name = models.CharField(max_length=50, verbose_name='Название дороги')
    carrier_name = models.CharField(max_length=50, verbose_name='Название перевозчика', choices=carriers)
    bid = models.CharField(max_length=50, verbose_name='Ставка')

    time_create = models.DateTimeField(auto_now_add=True)
    time_update = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Ставка {self.bid} по запросу {self.request}"

    class Meta:
        verbose_name = 'Ставки на запрос в логистику'
        verbose_name_plural = 'Ставки на запрос в логистику'
