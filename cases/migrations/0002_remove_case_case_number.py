# Generated by Django 3.0.3 on 2020-07-30 06:45

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('cases', '0001_initial'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='case',
            name='case_number',
        ),
    ]
