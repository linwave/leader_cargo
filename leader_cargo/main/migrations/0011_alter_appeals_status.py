# Generated by Django 3.2.20 on 2023-09-22 07:48

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0010_auto_20230921_1206'),
    ]

    operations = [
        migrations.AlterField(
            model_name='appeals',
            name='status',
            field=models.CharField(blank=True, max_length=50, null=True, verbose_name='Статус заявки'),
        ),
    ]