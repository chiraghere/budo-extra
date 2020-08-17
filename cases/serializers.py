from django.contrib.auth.models import User
from user.models import *
from user.serializers import *
from rest_framework import serializers
from rest_framework.validators import UniqueValidator
from .models import *


class case_serializer(serializers.ModelSerializer):
    class Meta:
        model = case
        fields = ['id', 'case_name', 'case_type', 'description']


class case_show_serializer(serializers.ModelSerializer):
    class Meta:
        model = case
        fields = ['id', 'case_name', 'case_members', 'case_clients', 'created_by', 'description', 'case_type', 'completed', 'created_at', 'updated_at']

    def show(self, validated_data):
        result = []
        for entry in validated_data:
            for element in entry['case_members']:
                user = User.objects.get(pk=int(element))        # members
                json = {'id': user.id, 'username': user.username, 'email': user.email}
                try:
                    user_profile = profile.objects.get(user=user)
                    serializer = profile_image_serializer(user_profile)
                    json['image'] = serializer.data
                    json['private'] = user_profile.private
                except:
                    json['image'] = None
                    json['private'] = None
                result.append(json)
            entry['case_members'] = result
            result = []

            element = entry['created_by']               # admin
            user = User.objects.get(pk=int(element))
            json = {'id': user.id, 'username': user.username, 'email': user.email}
            try:
                user_profile = profile.objects.get(user=user)
                serializer = profile_image_serializer(user_profile)
                json['image'] = serializer.data
                json['private'] = user_profile.private
            except:
                json['image'] = None
                json['private'] = None
            entry['created_by'] = json

        result = []
        for entry in validated_data:                    # clients
            for element in entry['case_clients']:
                user = User.objects.get(pk=int(element))
                json = {'id': user.id, 'username': user.username, 'email': user.email}
                try:
                    user_profile = profile.objects.get(user=user)
                    serializer = profile_image_serializer(user_profile)
                    json['image'] = serializer.data
                    json['private'] = user_profile.private
                except:
                    json['image'] = None
                    json['private'] = None
                result.append(json)
            entry['case_clients'] = result
            result = []

        return validated_data


class task_create_serializer(serializers.ModelSerializer):
    invoice_type = serializers.CharField(required=False, allow_null=True, allow_blank=True)

    class Meta:
        model = task
        fields = ['id', 'task_name', 'details', 'billing_type', 'invoice_type', 'cost', 'due_date']


class task_comments_serializer(serializers.ModelSerializer):
    class Meta:
        model = comments
        fields = ['id', 'task', 'comment', 'comment_user']


class task_checklist_serializer(serializers.ModelSerializer):
    class Meta:
        model = checklist
        fields = ['id', 'task', 'checklist_name', 'created_at', 'updated_at']


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
            'invoice_type',
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
        fields = ['id', 'task', 'start_time', 'end_time', 'time_spent', 'status']


class activity_serializer(serializers.ModelSerializer):
    class Meta:
        model = task_activity
        fields = ['id', 'user', 'action', 'task', 'created_at', 'target']


class case_invite_serializer(serializers.ModelSerializer):
    class Meta:
        model = invite
        fields = ['id',
                  'case',
                  'position']