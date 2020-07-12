from django.db import models


class subscription(models.Model):
    time_period_choice = (
        ('monthly', 'Monthly'),
        ('yearly', 'Yearly'),
        ('both', 'Both'),
    )
    name = models.CharField(max_length=64)
    case = models.IntegerField()
    case_member = models.IntegerField()
    case_clients = models.IntegerField()
    task = models.IntegerField()
    task_members = models.IntegerField()
    storage = models.IntegerField()
    time_period = models.CharField(choices=time_period_choice, max_length=16)
    monthly_amount = models.DecimalField(max_digits=10, decimal_places=2, null=True)
    yearly_amount = models.DecimalField(max_digits=10, decimal_places=2, null=True)
# Create your models here.
