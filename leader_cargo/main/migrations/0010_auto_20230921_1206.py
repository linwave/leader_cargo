# Generated by Django 3.2.20 on 2023-09-21 09:06

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0009_auto_20230920_1733'),
    ]

    operations = [
        migrations.AlterField(
            model_name='appeals',
            name='insurance_price',
            field=models.FloatField(blank=True, null=True, verbose_name='Страховка'),
        ),
        migrations.AlterField(
            model_name='appeals',
            name='logistic_price',
            field=models.FloatField(blank=True, null=True, verbose_name='Логистика'),
        ),
        migrations.AlterField(
            model_name='appeals',
            name='packaging_price',
            field=models.FloatField(blank=True, null=True, verbose_name='Упаковка'),
        ),
        migrations.AlterField(
            model_name='appeals',
            name='prr_price',
            field=models.FloatField(blank=True, null=True, verbose_name='ПРР'),
        ),
    ]