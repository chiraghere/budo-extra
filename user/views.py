from django.shortcuts import render
from django.http import JsonResponse
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.validators import UniqueValidator
from django.core.validators import validate_email
from rest_framework import status
from .serializers import *
from django.contrib.auth import authenticate
from rest_framework.authtoken.models import Token
from cases.models import *
from cases.serializers import *
from budo_admin.models import *
from budo_admin.serializers import *
from datetime import datetime, timedelta, date
from django.contrib.auth.models import User
from django.db.models import Q
from django.core.mail import send_mail
from django.urls import reverse

base_url = "http://127.0.0.1:8000"


class UserCreate(APIView):

    def post(self, request, format='json'):
        serializer = UserSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            if user:
                token = Token.objects.create(user=user)
                json = serializer.data
                json['token'] = token.key

                default_sub = subscription.objects.get(pk=1)
                sub = user_subscribe.objects.create(user=user, subscription=default_sub, time_period='none')
                sub.save()

                # flag = get_random_alphanumeric_string(16)
                # ver = user_verified.objects.create(user=user, flag=flag)
                # ver.save()
                #
                # reset_link = base_url + reverse('verify_account', args=(flag,))
                # send_mail(
                #     'Verify Account',
                #     'Click this link to verify the account.' + reset_link,
                #     'chirag2214@gmail.com',
                #     [user.email],
                #     fail_silently=False,
                # )

                return Response(json, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# class verify_account(APIView):
#
#     def get(self, request, flag):
#         ver = user_verified.objects.get(user=request.user)
#         if ver.flag == flag:
#             ver.verify = True
#             ver.save()
#             return JsonResponse({'Message': 'Account Verified'}, status=status.HTTP_200_OK)
#         else:
#             request.user.delete()
#             return JsonResponse({'Message': 'Error Invalid access led to account deletion'}, status=status.HTTP_400_BAD_REQUEST)


class Userlogin(APIView):

    def post(self, request, format='json'):
        data = request.data
        user = authenticate(request, username=data['username'], password=data['password'])
        if user:
            token = Token.objects.get(user=user)
            json = {'token': token.key}
            return Response(json, status=status.HTTP_200_OK)
        return Response({'Message': 'Invalid Username or Password'}, status=status.HTTP_400_BAD_REQUEST)


class edit_account(APIView):

    def put(self, request):
        try:
            exists = User.objects.filter(username=request.data['username'])
            if len(exists) == 0:
                request.user.username = request.data['username']
                request.user.save()
            else:
                return JsonResponse({'Message': 'Error Username must be unique'}, status=status.HTTP_400_BAD_REQUEST)
        except:
            pass

        try:
            try:
                validate_email(request.data['email'])
            except:
                return JsonResponse({'Message': 'Error Not a valid Email'}, status=status.HTTP_400_BAD_REQUEST)

            exists = User.objects.filter(username=request.data['email'])
            if len(exists) == 0:
                request.user.email = request.data['email']
                request.user.save()
            else:
                return JsonResponse({'Message': 'Error Email must be unique'}, status=status.HTTP_400_BAD_REQUEST)
        except:
            pass
        serializer = UserSerializer(request.user)
        return Response(serializer.data, status=status.HTTP_200_OK)


class edit_password(APIView):

    def put(self, request):
        user = authenticate(request, username=request.user.username, password=request.data['current_password'])
        if user:
            if len(request.data['new_password']) >= 8:
                request.user.set_password(request.data['new_password'])
                request.user.save()
                return JsonResponse({'Message': 'Password Change Successful'}, status=status.HTTP_200_OK)
            return JsonResponse({'Message': 'Error Password too short (At least 8 digits)'}, status=status.HTTP_400_BAD_REQUEST)
        return JsonResponse({'Message': 'Error Current Password did not match'}, status=status.HTTP_400_BAD_REQUEST)


class your_profile(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        serializer = UserSerializer(request.user)
        json = {'user_info': serializer.data}
        user_sub = user_subscribe.objects.get(user=request.user, status='current')
        json['subscription'] = {'id': user_sub.subscription.id, 'name': user_sub.subscription.name }
        try:
            profile_entry = profile.objects.get(user=request.user)
            serializer = profile_serializer(profile_entry)
            json['profile_info'] = serializer.data
            json['Profile_private'] = profile_entry.private
        except:
            json['Profile'] = "Null"

        json['closed_cases'] = len(request.user.case_members.exclude(completed__isnull=True)) + len(request.user.case_clients.exclude(completed__isnull=True))
        json['open_cases'] = len(request.user.case_members.filter(completed=None)) + len(request.user.case_clients.filter(completed=None))
        return Response(json, status=status.HTTP_200_OK)

    def post(self, request):
        try:
            request.data['dob'] = datetime.strptime(request.data['dob'], '%Y-%m-%d').date()
            if request.daya['dob'] >= date.today():
                request.data['dob'] = None
        except:
            pass
        serializer = profile_serializer(data=request.data)
        try:
            profile_entry = profile.objects.get(user=request.user)
            if serializer.is_valid():
                profile_entry.image = serializer.validated_data.get('image', profile_entry.image)
                profile_entry.first_name = serializer.validated_data.get('first_name', profile_entry.first_name)
                profile_entry.middle_name = serializer.validated_data.get('middle_name', profile_entry.middle_name)
                profile_entry.last_name = serializer.validated_data.get('last_name', profile_entry.last_name)
                profile_entry.organization = serializer.validated_data.get('organization', profile_entry.organization)
                profile_entry.dob = serializer.validated_data.get('dob', profile_entry.dob)
                profile_entry.gender = serializer.validated_data.get('gender', profile_entry.gender)
                profile_entry.address = serializer.validated_data.get('address', profile_entry.address)
                profile_entry.phone_number = serializer.validated_data.get('phone_number', profile_entry.phone_number)
                profile_entry.save()
                serializer = profile_serializer(profile_entry)
                return Response(serializer.data, status=status.HTTP_200_OK)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except:
            if serializer.is_valid():
                serializer.validated_data['user'] = request.user
                serializer.save()
                return Response(serializer.data, status=status.HTTP_201_CREATED)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class other_person_profile(APIView):

    def get(self, request, user_id):
        user = User.objects.get(pk=user_id)
        try:
            profile_entry = profile.objects.get(user=user)
            if profile_entry.private is True:
                return JsonResponse({"id": user.id, "username": user.username, "email": user.email}, status=status.HTTP_200_OK)
            else:
                serializer = profile_serializer(profile_entry)
                final = serializer.data
                final['id'] = user.id
                final['username'] = user.username
                final['email'] = user.email
                return JsonResponse(final, status=status.HTTP_200_OK)
        except:
            return JsonResponse({"id": user.id, "username": user.username, 'email': user.email}, status=status.HTTP_200_OK)


class profile_status(APIView):

    def get(self, request, action):
        try:
            profile_entry = profile.objects.get(user=request.user)
            if action == 'private':
                profile_entry.private = True
                profile_entry.save()
            elif action == 'public':
                profile_entry.private = False
                profile_entry.save()
            return JsonResponse({'Profile': action}, status=status.HTTP_200_OK)
        except:
            return JsonResponse({"Message": "Error Profile : Null"}, status=status.HTTP_400_BAD_REQUEST)


class show_invite(APIView):
    permission_classes = ([IsAuthenticated])

    def get(self, request):
        invite_set = invite.objects.filter(sent_to=request.user)
        serializer = case_invite_serializer(invite_set, many=True)
        for element in serializer.data:
            current_case = case.objects.get(pk=element['case'])
            element['case'] = current_case.case_name
            element['admin'] = current_case.created_by.username
        return Response(serializer.data, status=status.HTTP_200_OK)


class invite_decision(APIView):
    permission_classes = ([IsAuthenticated])

    def post(self, request, invite_id):
        try:
            invite_entry = invite.objects.get(pk=invite_id, sent_to=request.user)
            if request.data['status'] == 'accept':
                if invite_entry.position == 'case_member':
                    invite_entry.case.case_members.add(request.user)
                    invite_entry.case.save()
                    invite_entry.delete()
                    return JsonResponse({"Case Member": "Added"}, status=status.HTTP_200_OK)
                else:
                    invite_entry.case.case_clients.add(request.user)
                    invite_entry.case.save()
                    invite_entry.delete()
                    return JsonResponse({"Case Client": "Added"}, status=status.HTTP_200_OK)
            elif request.data['status'] == 'reject':
                invite_entry.delete()
                return JsonResponse({"Request": "Rejected"} , status=status.HTTP_200_OK)
        except:
            return JsonResponse({"Message": "Error Invalid Invite"}, status=status.HTTP_400_BAD_REQUEST)


class search(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        if len(request.data.get('info')) >= 3 and len(request.data.get('info'))is not None:
            username_results = User.objects.filter(Q(username__icontains=request.data.get('info')))[:10]
            email_results = User.objects.filter(Q(email__icontains=request.data.get('info')))[:10]
            records = (username_results | email_results).distinct()
            serializer = UserSerializer(records, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)
        else:
            return JsonResponse([], safe=False, status=status.HTTP_200_OK)


class view_subscriptions(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        sub_set = subscription.objects.all()
        serializer = subscription_serializer(sub_set, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class avail_subscriptions(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, sub_id):
        try:
            sub_entry = subscription.objects.get(pk=sub_id)
            existing_sub = user_subscribe.objects.get(user=request.user)

            if existing_sub.cost < sub_entry.monthly_amount or existing_sub.subscription.monthly_amount == 0:
                sub = user_subscribe.objects.create(user=request.user, subscription=sub_entry)
                sub.time_period = request.data['time_period']

                if request.data['time_period'] == 'monthly':
                    sub.expire = datetime.now() + timedelta(days=30)
                    sub.cost = sub_entry.monthly_amount
                elif request.data['time_period'] == 'yearly':
                    sub.expire = datetime.now() + timedelta(days=365)
                    sub.cost = sub_entry.yearly_amount

                existing_sub.status = 'previous'
                existing_sub.expire = datetime.now()
                existing_sub.save()

                try:
                    revenue_set = admin_revenue.objects.get(user=request.user)
                    revenue_set.amount = revenue_set.amount + sub.cost
                    revenue_set.save()
                except:
                    revenue_set = admin_revenue.objects.create(user=request.user)
                    revenue_set.amount = sub.cost
                    revenue_set.save()

                sub.save()

                return JsonResponse({"Subscription": "Added"}, status=status.HTTP_200_OK)
            else:
                return JsonResponse({"Message": " Error Subscription demotion is prohibited"}, status=status.HTTP_400_BAD_REQUEST)
        except:
            return JsonResponse({"Message": "Error Invalid Subscription"}, status=status.HTTP_400_BAD_REQUEST)


class view_your_subscription(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user_subscription_info = user_subscribe.objects.get(user=request.user, status='current')
        serializer = subscription_serializer(user_subscription_info.subscription)
        json = {'cost': user_subscription_info.cost, 'start_date': user_subscription_info.updated_at, 'end_date': user_subscription_info.expire}
        result = [serializer.data, json]
        return JsonResponse(result, safe=False, status=status.HTTP_200_OK)


