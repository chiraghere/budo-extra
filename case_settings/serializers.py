from django.contrib.auth.models import User
from rest_framework import serializers
from rest_framework.validators import UniqueValidator
from .models import *


class task_invoice_serializer(serializers.ModelSerializer):
    class Meta:
        model = task_invoice
        fields = ['id',
                  'task',
                  'total_cost',
                  'created_at',
                  'frequency',
                  'category']


class invoice_payment_serializer(serializers.ModelSerializer):
    class Meta:
        model = invoice_payment
        fields = ['id',
                  'payment_due_date',
                  'payment',
                  'status']

