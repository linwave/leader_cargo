from django.db import models


# class Leads(models.Model):
#     name_carrier = models.CharField(max_length=50, choices=carriers, verbose_name='Перевозчик')
#     file_path = models.FileField(verbose_name='Файлы перевозчиков', upload_to='files/cargo/%Y/%m/%d/', blank=False, null=False)
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
#