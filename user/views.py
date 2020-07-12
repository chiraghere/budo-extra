from django.shortcuts import render
from django.http import JsonResponse
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from .serializers import *
from django.contrib.auth import authenticate
from rest_framework.authtoken.models import Token
from cases.models import *
from cases.serializers import *
from datetime import datetime
from django.contrib.auth.models import User
from .models import *
from django.db.models import Q


class UserCreate(APIView):

    def post(self, request, format='json'):
        serializer = UserSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            if user:
                token = Token.objects.create(user=user)
                json = serializer.data
                json['token'] = token.key
                return Response(json, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class Userlogin(APIView):

    def post(self, request, format='json'):
        data = request.data
        user = authenticate(request, username=data['username'], password=data['password'])
        if user:
            token = Token.objects.get(user=user)
            json = {'token': token.key}
            return Response(json, status=status.HTTP_200_OK)
        return Response({'error': 'User does not exist'}, status=status.HTTP_400_BAD_REQUEST)


class your_profile(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        serializer = UserSerializer(request.user)
        json = [{'user_info': serializer.data}]
        try:
            profile_entry = profile.objects.get(user=request.user)
            serializer = profile_serializer(profile_entry)
            json.append({'profile_info': serializer.data})
        except:
            json.append({'profile_info': "Profile not filled yet"})
        return JsonResponse(json, safe=False)

    def post(self, request, format='json'):
        serializer = profile_serializer(data=request.data)
        if serializer.is_valid():
            serializer.validated_data['user'] = request.user
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def put(self, request):
        serializer = profile_serializer(data=request.data)
        profile_entry = profile.objects.get(user=request.user)
        if serializer.is_valid():
            profile_entry.first_name = serializer.validated_data.get('first_name', profile_entry.first_name)
            profile_entry.middle_name = serializer.validated_data.get('middle_name', profile_entry.middle_name)
            profile_entry.last_name = serializer.validated_data.get('last_name', profile_entry.last_name)
            profile_entry.organization = serializer.validated_data.get('organization', profile_entry.organization)
            profile_entry.dob = serializer.validated_data.get('dob', profile_entry.dob)
            profile_entry.save()
            serializer = profile_serializer(profile_entry)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class other_person_profile(APIView):

    def get(self, request, user_id):
        user = User.objects.get(pk=user_id)
        try:
            profile_entry = profile.objects.get(user=user)
            if profile_entry.private is True:
                return JsonResponse({"Username": user.username})
            else:
                dict1 = {'Username': user.username, 'Email': user.email, 'First Name': profile_entry.first_name, 'Last Name': profile_entry.last_name}
                return JsonResponse(dict1)
        except:
            return JsonResponse({"Username": user.username})


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
        except:
            return JsonResponse({"ERROR": "Create Profile First"})


class show_invite(APIView):
    permission_classes = ([IsAuthenticated])

    def get(self, request):
        invite_set = invite.objects.filter(sent_to=request.user)
        serializer = case_invite_serializer(invite_set, many=True)
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
                    return JsonResponse({"Case Member": "Added"})
                else:
                    invite_entry.case.case_clients.add(request.user)
                    invite_entry.case.save()
                    invite_entry.delete()
                    return JsonResponse({"Case Client": "Added"})
            elif request.data['status'] == 'reject':
                invite_entry.delete()
                return JsonResponse({"Request": "Rejected"})
        except:
            return JsonResponse({"ERROR": "Unauthorized User"})


class search(APIView):

    def post(self, request):
        if len(request.data.get('info')) >= 3 and len(request.data.get('info'))is not None:
            username_results = User.objects.filter(Q(username__icontains=request.data.get('info')))[:10]
            email_results = User.objects.filter(Q(email__icontains=request.data.get('info')))[:10]
            final_result = username_results.intersection(email_results)
            serializer = UserSerializer(final_result, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)
        else:
            return JsonResponse({"ALERT": "No result if letters entered are less than 3"})


class user_subscribe(APIView):

    def get(self, request):
        pass



# Create your views here.
