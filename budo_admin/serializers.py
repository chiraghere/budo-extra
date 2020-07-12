from django.contrib.auth.models import User
from rest_framework import serializers
from rest_framework.validators import UniqueValidator
from .models import *


class subscription_serializer(serializers.ModelSerializer):

    monthly_amount = serializers.DecimalField(required=False, allow_null=True, max_digits=10, decimal_places=2)
    yearly_amount = serializers.DecimalField(required=False, allow_null=True, max_digits=10, decimal_places=2)

    class Meta:
        model = subscription
        fields = ['id',
                  'name',
                  'case',
                  'case_member',
                  'case_clients',
                  'task',
                  'task_members',
                  'storage',
                  'time_period',
                  'monthly_amount',
                  'yearly_amount']