from django.db import models
from django.contrib.auth.models import User


class subscription(models.Model):
    name = models.CharField(max_length=64, unique=True)
    case = models.IntegerField()
    case_member = models.IntegerField()
    case_clients = models.IntegerField()
    task = models.IntegerField()
    storage = models.IntegerField()
    monthly_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    yearly_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)


class admin_revenue(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)


class to_do_list(models.Model):
    job = models.CharField(max_length=225)
    created_at = models.DateTimeField(auto_now_add=True)
    status = models.BooleanField(default=False)
# Create your models here.
