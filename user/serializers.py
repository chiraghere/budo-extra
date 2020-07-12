from django.contrib.auth.models import User
from rest_framework import serializers
from rest_framework.validators import UniqueValidator
from .models import *


class UserSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(
        required=True,
        validators=[UniqueValidator(queryset=User.objects.all())]
    )

    username = serializers.CharField(
        required=True,
        validators=[UniqueValidator(queryset=User.objects.all())]
    )

    password = serializers.CharField(min_length=8, write_only=True)

    def create(self, validated_data):
        user = User.objects.create_user(
            username=validated_data['username'],
            email=validated_data['email'],
            password=validated_data['password']
        )
        return user

    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'password']


class profile_serializer(serializers.ModelSerializer):

    first_name = serializers.CharField(required=False, allow_null=True, allow_blank=True)
    last_name = serializers.CharField(required=False, allow_null=True, allow_blank=True)
    middle_name = serializers.CharField(required=False, allow_null=True, allow_blank=True)
    organization = serializers.CharField(required=False, allow_null=True, allow_blank=True)
    dob = serializers.DateTimeField(required=False, allow_null=True)

    class Meta:
        model = profile
        fields = ['first_name', 'middle_name', 'last_name', 'organization', 'dob']