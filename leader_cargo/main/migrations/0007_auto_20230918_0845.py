# Generated by Django 3.2.20 on 2023-09-18 05:45

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0006_auto_20230916_1509'),
    ]

    operations = [
        migrations.AlterField(
            model_name='goods',
            name='link_url',
            field=models.CharField(blank=True, max_length=200, null=True, verbose_name='Ссылка на товар'),
        ),
        migrations.AlterField(
            model_name='goods',
            name='price_rmb',
            field=models.FloatField(blank=True, null=True, verbose_name='Цена товара в Китае в юанях'),
        ),
        migrations.AlterField(
            model_name='goods',
            name='product_description',
            field=models.CharField(blank=True, max_length=500, null=True, verbose_name='Описание товара'),
        ),
        migrations.AlterField(
            model_name='goods',
            name='quantity',
            field=models.FloatField(blank=True, null=True, verbose_name='Количество'),
        ),
    ]