# Generated by Django 3.0.3 on 2020-08-01 07:52

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('cases', '0003_auto_20200731_1641'),
    ]

    operations = [
        migrations.AlterField(
            model_name='task',
            name='cost',
            field=models.DecimalField(decimal_places=2, default=0, max_digits=10),
        ),
        migrations.AlterField(
            model_name='task',
            name='details',
            field=models.TextField(default=''),
        ),
        migrations.AlterField(
            model_name='task',
            name='invoice_type',
            field=models.CharField(choices=[('hourly', 'Hourly'), ('onetime', 'Onetime')], max_length=16, null=True),
        ),
    ]
