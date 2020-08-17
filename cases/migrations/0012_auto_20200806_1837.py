# Generated by Django 3.0.3 on 2020-08-06 13:07

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('cases', '0011_task_completed'),
    ]

    operations = [
        migrations.AlterField(
            model_name='task',
            name='billing_type',
            field=models.CharField(choices=[('non billing', 'Non Billing'), ('billing', 'Billing')], default='non billing', max_length=16, null=True),
        ),
    ]
