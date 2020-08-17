from django.db import models
from django.contrib.auth.models import User
from budo_admin.models import subscription
import random
import string


def get_random_alphanumeric_string(length):
    letters_and_digits = string.ascii_letters + string.digits
    result_str = ''.join((random.choice(letters_and_digits) for i in range(length)))
    return result_str


class user_verified(models.Model):
    verify = models.BooleanField(default=False)
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    flag = models.CharField(max_length=16)


class profile(models.Model):
    gender_choices = (
        ('male', 'Male'),
        ('female', 'Female'),
        ('other', 'Other')
    )
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    image = models.ImageField(upload_to='profile_images', blank=True, null=True)
    first_name = models.CharField(max_length=64, null=True)
    middle_name = models.CharField(max_length=64, null=True)
    last_name = models.CharField(max_length=64, blank=True, null=True)
    organization = models.CharField(max_length=64, blank=True, null=True)
    dob = models.DateField(null=True)
    gender = models.CharField(choices=gender_choices, max_length=6, null=True)
    phone_number = models.CharField(max_length=12, null=True)
    address = models.CharField(max_length=64, null=True)
    private = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


class user_subscribe(models.Model):
    time_period_choices = (
        ('monthly', 'Monthly'),
        ('yearly', 'Yearly'),
        ('none', 'None'),
    )
    status_choice = (
        ('current', 'Current'),
        ('previous', 'Previous'),
    )
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    subscription = models.ForeignKey(subscription, on_delete=models.CASCADE)
    time_period = models.CharField(choices=time_period_choices, default='none', max_length=16)
    cost = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    updated_at = models.DateTimeField(auto_now=True)
    expire = models.DateTimeField(null=True)
    status = models.CharField(choices=status_choice, max_length=10, default='current')
# Create your models here.
