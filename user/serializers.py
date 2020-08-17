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

    image = serializers.ImageField(allow_null=True, required=False)
    first_name = serializers.CharField(required=False, allow_null=True, allow_blank=True)
    last_name = serializers.CharField(required=False, allow_null=True, allow_blank=True)
    middle_name = serializers.CharField(required=False, allow_null=True, allow_blank=True)
    organization = serializers.CharField(required=False, allow_null=True, allow_blank=True)
    dob = serializers.DateField(required=False, allow_null=True)
    gender = serializers.CharField(required=False, allow_null=True)
    phone_number = serializers.CharField(required=False, allow_null=True)
    address = serializers.CharField(required=False, allow_null=True)

    class Meta:
        model = profile
        fields = ['first_name', 'middle_name', 'last_name', 'organization', 'dob', 'gender', 'phone_number', 'address', 'image']


class profile_image_serializer(serializers.ModelSerializer):

    class Meta:
        model = profile
        fields = ['image']