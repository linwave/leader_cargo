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