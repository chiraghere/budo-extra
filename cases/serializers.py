from django.contrib.auth.models import User
from rest_framework import serializers
from rest_framework.validators import UniqueValidator
from .models import *


class case_serializer(serializers.ModelSerializer):
    class Meta:
        model = case
        fields = ['id', 'case_name']


class case_show_serializer(serializers.ModelSerializer):
    class Meta:
        model = case
        fields = ['id', 'case_name', 'case_members', 'case_clients', 'created_by']


class task_create_serializer(serializers.ModelSerializer):
    class Meta:
        model = task
        fields = ['id', 'task_name']


class task_comments_serializer(serializers.ModelSerializer):
    class Meta:
        model = comments
        fields = ['id', 'task', 'comment', 'comment_user']


class task_checklist_serializer(serializers.ModelSerializer):
    class Meta:
        model = checklist
        fields = ['id', 'task', 'checklist_name']


class checklist_items_serializer(serializers.ModelSerializer):
    class Meta:
        model = checklist_items
        fields = ['id', 'checklist', 'item', 'updated_at']


class task_images(serializers.ModelSerializer):
    class Meta:
        model = image
        fields = ['id', 'image']


class task_documents(serializers.ModelSerializer):
    class Meta:
        model = document
        fields = ['id', 'document']


class task_label_serializer(serializers.ModelSerializer):
    class Meta:
        model = task_labels
        fields = ['id', 'label']


class task_show_serializer(serializers.ModelSerializer):

    class Meta:
        model = task
        fields = [
            'id',
            'task_name',
            'details',
            'due_date',
            'billing_type',
            'cost',
            'task_members',
            'task_case',
            'created_by',
            'created_at',
            'updated_at',
        ]


class timer_serializer(serializers.ModelSerializer):
    class Meta:
        model = timer
        fields = ['id', 'task', 'start_time', 'end_time', 'status']


class activity_serializer(serializers.ModelSerializer):
    class Meta:
        model = task_activity
        fields = ['id', 'user', 'action', 'task', 'created_at']


class case_invite_serializer(serializers.ModelSerializer):
    class Meta:
        model = invite
        fields = ['id',
                  'case',
                  'position']