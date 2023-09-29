from django.db import models


class CargoFiles(models.Model):
    carriers = [
        ('Ян', 'Ян'),
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
    article = models.CharField(max_length=50, verbose_name='Артикул')
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

    cargo_id = models.ForeignKey('CargoFiles', on_delete=models.PROTECT)

    time_create = models.DateTimeField(auto_now_add=True)
    time_update = models.DateTimeField(auto_now=True)
    status = models.CharField(max_length=50, default='В пути', choices=statuses, verbose_name='Статус', blank=True, null=True)

    def __str__(self):
        return f"{self.article} {self.status}"

    class Meta:
        verbose_name = 'Артикула'
        verbose_name_plural = 'Артикула'
