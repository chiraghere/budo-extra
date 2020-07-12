from django.shortcuts import render, redirect
from .models import *
from django.http import HttpResponse
from django.http import JsonResponse
from rest_framework.views import APIView
from rest_framework.response import Response
from django.views import View
from rest_framework.permissions import IsAuthenticated
from django.contrib.auth.models import User
from cases.models import *
from cases.serializers import *
from datetime import datetime
from chat.models import *
from chat.serializer import *
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
import json
import zipfile
from chat.views import *
from user.serializers import *
from user.models import *
import os
from django.core.mail import send_mail, EmailMessage
from rest_framework import status
from rest_framework.authtoken.models import Token
from .serializers import *
from rest_framework.permissions import IsAuthenticated
from django.contrib.auth import authenticate


class admin_login(View):

    def get(self, request):
        return render(request, 'login.html')

    def post(self, request, format='json'):
        data = request.POST
        user = authenticate(request, username=data['username'], password=data['password'])
        try:
            if user.is_staff:
                login(request, user)
                return redirect('/budo_admin/all_users/')
            return redirect('/budo_admin/admin_login/')
        except:
            return redirect('/budo_admin/admin_login/')


@method_decorator(login_required, name='get')
class admin_logout(View):

    def get(self, request):
        logout(request)
        return redirect('/budo_admin/admin_login/')


@method_decorator(login_required, name='get')
class all_users(View):

    def get(self, request):
        if request.user.is_superuser:
            user_list = User.objects.all()
            result = []
            serializer = UserSerializer(user_list, many=True)
            for (user, entry) in zip(user_list, serializer.data):
                if user.is_authenticated:
                    entry['status'] = 'Online'
                else:
                    entry['status'] = 'Offline'
                dict2 = {'member': user.case_members.all(), 'client': user.case_clients.all(),
                         'admin': case.objects.filter(created_by=user)}
                dict1 = {'Cases': dict2}

            return render(request, 'user_list.html', {'pop': serializer.data, 'case_info': dict1})


@method_decorator(login_required, name='get')
@method_decorator(login_required, name='post')
class get_user_profile(View):

    def get(self, request):
        return render(request, 'user.html')

    def post(self, request):
        user_username = User.objects.filter(username=request.POST.get('username'))
        try:
            user_id = User.objects.filter(pk=request.POST.get('id'))
        except:
            user_id = User.objects.filter(email='error')

        if request.POST.get('email') is not '':
            user_email = User.objects.filter(email=request.POST.get('email'))
        else:
            user_email = User.objects.filter(email='error')

        user_username = user_username.union(user_email)
        user_result = user_username.union(user_id)
        if len(user_result) == 1:
            for user in user_result:
                return redirect('get_user', user_id=user.id)
        return redirect('/budo_admin/get_user_profile/')


@method_decorator(login_required, name='get')
class get_user(View):

    def get(self, request, user_id):
        # try:
            user = User.objects.get(pk=int(user_id))
            try:
                user_profile = profile.objects.get(user=user)
                user_case_members = user.case_members.all()
                user_case_clients = user.case_clients.all()
                user_case_admin = case.objects.filter(created_by=user)
            except:
                user_profile = 'Empty'
                user_case_members = user.case_members.all()
                user_case_clients = user.case_clients.all()
                user_case_admin = case.objects.filter(created_by=user)

            return render(request, 'user_details.html', {'user_info': user, 'profile_info': user_profile, 'user_case_members': user_case_members,
                                                         'user_case_clients': user_case_clients, 'user_case_admin': user_case_admin})
        # except:
        #     return redirect('/budo_admin/all_users/')


@method_decorator(login_required, name='get')
class subscription_view(View):

    def get(self, request):
        sub_set = subscription.objects.all()
        serializer = subscription_serializer(sub_set, many=True)
        return render(request, 'subscription.html', {'pop': serializer.data})


@method_decorator(login_required, name='get')
@method_decorator(login_required, name='post')
class add_subscription(View):

    def get(self, request):
        return render(request, 'add_subscription.html')

    def post(self, request):
        if request.user.is_superuser:
            data = request.POST
            if request.POST['Time Period'] == 'Monthly':
                sub_obj = subscription.objects.create(name=data['name'], case=data['case'], case_member=data['case_member'], case_clients=data['case_clients']
                                                      , task=data['task'], task_members=data['task_members'], storage=data['storage'],
                                                      time_period=data['Time Period'], monthly_amount=data['monthly_amount'])
                sub_obj.save()
                return redirect('/budo_admin/subscription/')
            if request.POST['Time Period'] == 'Yearly':
                sub_obj = subscription.objects.create(name=data['name'], case=data['case'], case_member=data['case_member'], case_clients=data['case_clients']
                                                      , task=data['task'], task_members=data['task_members'], storage=data['storage'],
                                                      time_period=data['Time Period'], yearly_amount=data['yearly_amount'])
                sub_obj.save()
                return redirect('/budo_admin/subscription/')
            if request.POST['Time Period'] == 'Both':
                sub_obj = subscription.objects.create(name=data['name'], case=data['case'], case_member=data['case_member'], case_clients=data['case_clients']
                                                      , task=data['task'], task_members=data['task_members'], storage=data['storage'],
                                                      time_period=data['Time Period'], monthly_amount=data['monthly_amount'], yearly_amount=data['yearly_amount'])
                sub_obj.save()
                return redirect('/budo_admin/subscription/')
        else:
            return redirect('/budo_admin/admin_login/')


class get_subscription(View):

    def get(self, request, sub_id):
        if request.user.is_superuser:
            try:
                sub_entry = subscription.objects.get(pk=sub_id)
                pass
            except:
                pass


@method_decorator(login_required, name='get')
class all_cases(View):

    def get(self, request):
        if request.user.is_superuser:
            case_set = case.objects.all()
            return render(request, 'case_list.html', {'pop': case_set})
        return redirect('/budo_admin/admin_login/')


@method_decorator(login_required, name='get')
class get_case(View):

    def get(self, request, case_id):
        if request.user.is_superuser:
            try:
                case_entry = case.objects.get(pk=case_id)
                task_set = task.objects.filter(task_case=case_entry)
                return render(request, 'case_details.html', {'case': case_entry, 'task': task_set})
            except:
                return redirect('/budo_admin/all_cases/')
        return redirect('/budo_admin/admin_login/')

