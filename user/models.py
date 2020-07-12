from django.db import models
from django.contrib.auth.models import User
from budo_admin.models import subscription


class profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    first_name = models.CharField(max_length=64, null=True)
    middle_name = models.CharField(max_length=64, null=True)
    last_name = models.CharField(max_length=64, blank=True, null=True)
    organization = models.CharField(max_length=64, blank=True, null=True)
    dob = models.DateTimeField(null=True, blank=True)
    private = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


class user_subscribe(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    subscription = models.OneToOneField(subscription, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
# Create your models here.
