import datetime
import os
import uuid

from django.db import models
from django.urls import reverse
from main.models import CustomUser


def get_file_path(instance, filename):
    ext = filename.split('.')[-1]
    filename = "%s.%s" % (uuid.uuid4(), ext)
    return os.path.join(instance.directory_string_var, filename)


class Entity(models.Model):
    types = [
        ('ООО', 'ООО'),
        ('ИП', 'ИП'),
    ]
    name = models.CharField(max_length=255, verbose_name='Название')
    type = models.CharField(max_length=100, verbose_name='Тип', choices=types)
    inn = models.IntegerField(verbose_name='ИНН')
    cpp = models.IntegerField(verbose_name='КПП', blank=True, null=True)
    ogrnip = models.IntegerField(verbose_name='ОГРНИП', blank=True, null=True)
    ur_address = models.CharField(max_length=455, verbose_name='Юридический адрес')
    fact_address = models.CharField(max_length=455, verbose_name='Фактический адрес')
    phone = models.IntegerField(verbose_name='Телефон')
    name_job = models.CharField(max_length=255, verbose_name='Наименование должности', blank=True, null=True)
    fio = models.CharField(max_length=255, verbose_name='ФИО')
    based_charter = models.CharField(max_length=255, verbose_name='На основании', default='Устава', blank=True, null=True)
    nds_status = models.CharField(max_length=255, verbose_name='Статус НДС')

    time_create = models.DateTimeField(auto_now_add=True)
    time_update = models.DateTimeField(auto_now=True)
    status = models.BooleanField(default=True, blank=True, null=True)

    def __str__(self):
        return f"{self.name}"

    def get_absolute_url_entity(self):
        return reverse('bills:entity_edit', kwargs={'entity_id': self.pk})

    def phone_mask(self):
        phone = str(self.phone)
        if phone[0] == '7':
            pass
        else:
            pass
        return phone

    class Meta:
        verbose_name = 'Наше Юр. лицо'
        verbose_name_plural = 'Наши Юр. лица'
        ordering = ['-time_update']


class Clients(models.Model):
    manager = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, null=True, related_name="organizations")

    types = [
        ('ООО', 'ООО'),
        ('ИП', 'ИП'),
    ]
    name = models.CharField(max_length=255, verbose_name='Название')
    type = models.CharField(max_length=100, verbose_name='Тип', choices=types)
    inn = models.IntegerField(verbose_name='ИНН')
    cpp = models.IntegerField(verbose_name='КПП', blank=True, null=True)
    ogrnip = models.IntegerField(verbose_name='ОГРНИП', blank=True, null=True)
    ur_address = models.CharField(max_length=455, verbose_name='Юридический адрес')
    fact_address = models.CharField(max_length=455, verbose_name='Фактический адрес')
    phone = models.IntegerField(verbose_name='Телефон')
    name_job = models.CharField(max_length=255, verbose_name='Наименование должности', blank=True, null=True)
    fio = models.CharField(max_length=255, verbose_name='ФИО')
    based_charter = models.CharField(max_length=255, verbose_name='На основании', default='Устава', blank=True, null=True)
    nds_status = models.CharField(max_length=255, verbose_name='Статус НДС')

    time_create = models.DateTimeField(auto_now_add=True)
    time_update = models.DateTimeField(auto_now=True)
    status = models.BooleanField(default=True, blank=True, null=True)

    def __str__(self):
        return f"{self.name}"

    def get_absolute_url_client(self):
        return reverse('bills:clients_edit', kwargs={'client_id': self.pk})


    def phone_mask(self):
        phone = str(self.phone)
        if phone[0] == '7':
            pass
        else:
            pass
        return phone

    class Meta:
        verbose_name = 'Клиент'
        verbose_name_plural = 'Клиенты'
        ordering = ['-time_update']


class RequisitesClients(models.Model):
    client = models.ForeignKey(Clients, on_delete=models.CASCADE, related_name='requisites')

    name = models.CharField(max_length=255, verbose_name='Название реквизитов')
    rs = models.IntegerField( verbose_name='Р/с')
    bic = models.IntegerField(verbose_name='БИК')
    ks = models.IntegerField(verbose_name='К/с')
    name_bank = models.CharField(max_length=255, verbose_name='Название банка')

    time_create = models.DateTimeField(auto_now_add=True)
    time_update = models.DateTimeField(auto_now=True)
    status = models.BooleanField(default=True, blank=True, null=True)

    def __str__(self):
        return f"{self.name}"

    class Meta:
        verbose_name = 'Реквизит клиента'
        verbose_name_plural = 'Реквизиты клиентов'
        ordering = ['-time_update']


class RequisitesEntity(models.Model):
    entity = models.ForeignKey(Entity, on_delete=models.CASCADE, related_name='requisites')

    name = models.CharField(max_length=255, verbose_name='Название реквизитов')
    rs = models.IntegerField( verbose_name='Р/с')
    bic = models.IntegerField(verbose_name='БИК')
    ks = models.IntegerField(verbose_name='К/с')
    name_bank = models.CharField(max_length=255, verbose_name='Название банка')

    time_create = models.DateTimeField(auto_now_add=True)
    time_update = models.DateTimeField(auto_now=True)
    status = models.BooleanField(default=True, blank=True, null=True)

    def __str__(self):
        return f"{self.name}"

    class Meta:
        verbose_name = 'Наш реквизит'
        verbose_name_plural = 'Наши реквизиты'
        ordering = ['-time_update']


class Bills(models.Model):
    statuses = [
        ('Черновик', 'Черновик'),
        ('Новый', 'Новый'),
        ('Переделать запрос', 'Переделать запрос'),
        ('В обработке', 'В обработке'),
        ('Исполнено', 'Исполнено'),
        ('Возвращено в обработку', 'Возвращено в обработку')
    ]
    types = [
        ('ООО', 'ООО'),
        ('ИП', 'ИП'),
    ]
    types_nds = [
        ('с НДС', 'с НДС'),
        ('без НДС', 'без НДС'),
    ]
    manager = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, null=True)
    client = models.ForeignKey(Clients, on_delete=models.SET_NULL, null=True)
    entity = models.ForeignKey(Entity, on_delete=models.SET_NULL, null=True)
    status = models.CharField(max_length=50, choices=statuses, verbose_name='Статус', default='Черновик', blank=True, null=True)
    nds_status = models.CharField(max_length=50, choices=types_nds, verbose_name='Статус НДС', blank=True, null=True)
    summa = models.FloatField(verbose_name='Сумма')

    comments_manager = models.CharField(max_length=600, verbose_name='Комментарий менеджера', blank=True, null=True)
    comments_booker = models.CharField(max_length=600, verbose_name='Комментарий бухгалтера', blank=True, null=True)

    time_create = models.DateTimeField(auto_now_add=True)
    time_update = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Счёт {self.client}"

    def get_absolute_url_bill(self):
        return reverse('bills:bills_edit', kwargs={'bill_id': self.pk})

    class Meta:
        verbose_name = 'Счет'
        verbose_name_plural = 'Счета'
        ordering = ['-time_update']


class BillsFiles(models.Model):
    directory_string_var = f'files/bills/{datetime.datetime.now().strftime("%Y/%m/%d/")}'
    bill = models.ForeignKey(Bills, on_delete=models.CASCADE)
    name = models.CharField(max_length=255, verbose_name='Название файла', blank=True, null=True)
    file_path_request = models.FileField(verbose_name='Файл по счету',
                                         upload_to=get_file_path, blank=True, null=True)

    time_create = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Файл по счету {self.bill}"

    class Meta:
        verbose_name = 'Файл по счету'
        verbose_name_plural = 'Файлы по счетам'


class BillsGoods(models.Model):
    bill = models.ForeignKey(Bills, on_delete=models.CASCADE)
    name = models.CharField(max_length=255, verbose_name='Наименование', blank=True, null=True)
    quantity = models.IntegerField(verbose_name='Количество', blank=True, null=True)
    summa = models.FloatField(verbose_name='Сумма', blank=True, null=True)

    time_create = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Товар по счету {self.bill}"

    class Meta:
        verbose_name = 'Товар по счету'
        verbose_name_plural = 'Товары по счетам'

