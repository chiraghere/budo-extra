from django.db import models
from cases.models import *
from django.core.validators import MaxValueValidator, MinValueValidator


class task_invoice(models.Model):
    invoice_choices = (
        ('single', 'Single'),
        ('equal', 'equal'),
        ('random', 'Random'),
    )
    task = models.OneToOneField(task, on_delete=models.CASCADE, related_name='task_invoice')
    total_cost = models.DecimalField(max_digits=10, decimal_places=2)
    frequency = models.IntegerField(validators=[MinValueValidator(0), MaxValueValidator(10)], default=1,)
    category = models.CharField(choices=invoice_choices, default='single', max_length=6)
    created_at = models.DateTimeField(auto_now_add=True)


class invoice_payment(models.Model):
    invoice = models.ForeignKey(task_invoice, on_delete=models.CASCADE, related_name='invoice_payment')
    due_date = models.DateField(null=True)
    payment = models.DecimalField(max_digits=10, decimal_places=2, null=True)
    status = models.BooleanField(default=False)


# Create your models here.
