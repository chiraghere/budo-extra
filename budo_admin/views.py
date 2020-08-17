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
from datetime import datetime, timedelta
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
            date_from = datetime.now() - timedelta(days=1)
            new_users = User.objects.filter(date_joined__gte=date_from)
            user_list = User.objects.all().order_by('-date_joined')
            result = []
            serializer = UserSerializer(user_list, many=True)
            for (user, entry) in zip(user_list, serializer.data):
                if user.is_authenticated and user.username != 'admin':
                    entry['date_joined'] = user.date_joined
                    sub = user_subscribe.objects.get(user=user, status='current')
                    entry['subscription'] = sub.subscription.name
                else:
                    entry['status'] = 'Inactive'
                dict2 = {'member': user.case_members.all(), 'client': user.case_clients.all(),
                         'admin': case.objects.filter(created_by=user)}
                dict1 = {'Cases': dict2}

            return render(request, 'user_list.html', {'pop': serializer.data, 'case_info': dict1, 'new_users': new_users})


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
        revenue_amt = 0
        try:
            user = User.objects.get(pk=int(user_id))
            try:
                user_profile = profile.objects.get(user=user)
            except:
                user_profile = 'Empty'

            user_case_members = user.case_members.all()
            user_case_clients = user.case_clients.all()
            user_case_admin = case.objects.filter(created_by=user)
            subscription_set = user_subscribe.objects.get(user=user, status='current')
            revenue_set = user_subscribe.objects.filter(user=user)
            for entry in revenue_set:
                revenue_amt = revenue_amt + entry.cost

            return render(request, 'user_details.html', {'user_info': user, 'profile_info': user_profile, 'user_case_members': user_case_members,
                                                         'user_case_clients': user_case_clients, 'user_case_admin': user_case_admin,
                                                         'subscription': subscription_set, 'revenue': revenue_amt, 'bills': revenue_set})
        except:
            return redirect('/budo_admin/all_users/')


@method_decorator(login_required, name='get')
class subscription_view(View):

    def get(self, request):
        list1 = []
        date_from = datetime.now() - timedelta(days=1)
        sub_set = subscription.objects.all()
        serializer = subscription_serializer(sub_set, many=True)

        for element, entry in zip(sub_set, serializer.data):
            list1.append(user_subscribe.objects.filter(subscription=element))
            entry['user_length'] = list1
            list1 = []

        try:
            default_sub = subscription.objects.get(name='default')
            new_users_sub = user_subscribe.objects.filter(updated_at__gte=date_from).exclude(subscription=default_sub)
            sub_users = user_subscribe.objects.all().exclude(subscription=default_sub)
        except:
            sub_users = []
            new_users_sub = []

        return render(request, 'subscription.html', {'pop': serializer.data, 'new_subs': new_users_sub, 'premium_users': sub_users})


@method_decorator(login_required, name='get')
@method_decorator(login_required, name='post')
class add_subscription(View):

    def get(self, request):
        return render(request, 'add_subscription.html')

    def post(self, request):
        if request.user.is_superuser:
            data = request.POST
            sub_obj = subscription.objects.create(name=data['name'], case=data['case'], case_member=data['case_member'], case_clients=data['case_clients']
                                                  , task=data['task'], storage=data['storage'],
                                                  monthly_amount=data['monthly_amount'], yearly_amount=data['yearly_amount'])
            sub_obj.save()
            return redirect('/budo_admin/subscription/')
        else:
            return redirect('/budo_admin/admin_login/')


@method_decorator(login_required, name='get')
class get_subscription(View):

    def get(self, request, sub_id):
        if request.user.is_superuser:
            try:
                sub_entry = subscription.objects.get(pk=sub_id)
                users_sub = user_subscribe.objects.filter(subscription=sub_entry)
                return render(request, 'subscription_details.html', {'subscription': sub_entry, 'user': users_sub})
            except:
                return render(request, '/budo_admin/subscription/')
        return render(request, '/budo_admin/subscription/')


@method_decorator(login_required, name='get')
class all_cases(View):

    def get(self, request):
        if request.user.is_superuser:
            case_set = case.objects.all().order_by('-updated_at')
            date_from = datetime.now() - timedelta(days=1)
            new_cases = case.objects.filter(updated_at__gte=date_from)
            return render(request, 'case_list.html', {'pop': case_set, 'new_cases': new_cases})
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


@method_decorator(login_required, name='get')
class dashboard(View):

    def get(self, request):
        if request.user.is_superuser:
            revenue = 0

            date_from = datetime.now() - timedelta(days=1)
            new_users = User.objects.filter(date_joined__gte=date_from)
            default_sub = subscription.objects.get(name='default')
            new_users_sub = user_subscribe.objects.filter(updated_at__gte=date_from).exclude(subscription=default_sub)
            sub_users = user_subscribe.objects.all().exclude(subscription=default_sub)

            for user in new_users_sub:
                revenue = revenue + user.cost

            new_cases = case.objects.filter(updated_at__gte=date_from)

            sub_set = subscription.objects.all()

            todo_list = to_do_list.objects.filter(status=False)

            return render(request, 'dashboard.html', {'sub_users': sub_users, 'new_users': new_users, 'revenue': revenue, 'cases': new_cases,
                                                      'sub': sub_set, 'todo': todo_list, 'new_users_sub': new_users_sub})


@method_decorator(login_required, name='get')
class revenue(View):

    def get(self, request):
        revenue_total = 0
        revenue_today = 0
        result = []
        date_from = datetime.now() - timedelta(days=1)

        default_sub = subscription.objects.get(name='default')
        users_sub = user_subscribe.objects.all().exclude(subscription=default_sub)
        for user in users_sub:
            revenue_total = revenue_total + user.cost

        new_users_sub = user_subscribe.objects.filter(updated_at__gte=date_from).exclude(subscription=default_sub)
        for user in new_users_sub:
            revenue_today = revenue_today + user.cost

        users_revenue = admin_revenue.objects.all().order_by('-amount')
        for entry in users_revenue:
            sub = user_subscribe.objects.get(user=entry.user, status='current')
            dict1 = {'id': entry.user.id, 'username': entry.user.username, 'subscription': sub.subscription.name,
                     'revenue': entry.amount, 'date_joined': entry.user.date_joined}
            result.append(dict1)

        return render(request, 'revenue.html', {'users_sub': result, 'revenue_total': revenue_total, 'revenue_today': revenue_today})