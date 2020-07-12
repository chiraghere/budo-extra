from django.contrib.auth.models import User
from rest_framework import serializers
from .models import *


class chat_serializer(serializers.ModelSerializer):
    class Meta:
        model = chat
        fields = ['id', 'case', 'chat_name', 'chat_members']


class message_serializer(serializers.ModelSerializer):
    class Meta:
        model = message
        fields = ['id', 'content', 'created_by', 'created_at']