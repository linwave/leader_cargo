# Generated by Django 3.2.20 on 2023-10-05 12:13

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('analytics', '0003_alter_cargoarticle_status'),
    ]

    operations = [
        migrations.AddField(
            model_name='cargoarticle',
            name='paid_by_the_client_status',
            field=models.CharField(blank=True, choices=[('Оплачено полностью', 'Оплачено полностью'), ('Оплачено частично', 'Оплачено частично'), ('Не оплачено', 'Не оплачено')], default='Не оплачено', max_length=50, null=True, verbose_name='Оплачено клиентом'),
        ),
        migrations.AddField(
            model_name='cargoarticle',
            name='payment_to_the_carrier_status',
            field=models.CharField(blank=True, choices=[('Оплачено', 'Оплачено'), ('Не оплачено', 'Не оплачено')], default='Не оплачено', max_length=50, null=True, verbose_name='Оплата перевозчику'),
        ),
        migrations.AddField(
            model_name='cargoarticle',
            name='prr',
            field=models.CharField(blank=True, max_length=50, null=True, verbose_name='ПРР'),
        ),
        migrations.AddField(
            model_name='cargoarticle',
            name='tat_cost',
            field=models.CharField(blank=True, max_length=50, null=True, verbose_name='Оплата ТАТ'),
        ),
        migrations.AddField(
            model_name='cargoarticle',
            name='time_cargo_arrival_to_RF',
            field=models.DateTimeField(blank=True, null=True, verbose_name='Дата прибытия груза в РФ'),
        ),
        migrations.AddField(
            model_name='cargoarticle',
            name='time_cargo_release',
            field=models.DateTimeField(blank=True, null=True, verbose_name='Дата выдачи груза'),
        ),
        migrations.AlterField(
            model_name='cargoarticle',
            name='status',
            field=models.CharField(blank=True, choices=[('В пути', 'В пути'), ('Прибыл в РФ', 'Прибыл в РФ')], default='В пути', max_length=50, null=True, verbose_name='Статус'),
        ),
    ]