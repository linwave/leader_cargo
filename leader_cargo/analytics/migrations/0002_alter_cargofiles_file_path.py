# Generated by Django 3.2.20 on 2023-09-26 12:50

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('analytics', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='cargofiles',
            name='file_path',
            field=models.FileField(upload_to='files/cargo/%Y/%m/%d/', verbose_name='Файлы перевозчиков'),
        ),
    ]