# Generated by Django 3.0.3 on 2020-08-04 03:49

import cases.models
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('cases', '0008_auto_20200804_0913'),
    ]

    operations = [
        migrations.AlterField(
            model_name='image',
            name='image',
            field=models.ImageField(max_length=500, upload_to=cases.models.path_file_name),
        ),
    ]