from django.shortcuts import render, redirect
from django.http import JsonResponse
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from .serializer import *
from django.contrib.auth import authenticate
from rest_framework.authtoken.models import Token
from django.views import View
from django.contrib.auth.models import User
from .models import *
from datetime import datetime
from cases.models import case
from user.serializers import *
from user.models import *
from .consumers import ChatConsumer
import json


def case_user_flag(case_obj, user):
    for member in case_obj.case_members.all():
        if user.id == member.id:  # (flag) check if the user is member of the case
            return True


def case_client_flag(case_obj, user):
    for member in case_obj.case_clients.all():
        if user.id == member.id:  # (flag) check if the user is client of the case
            return True


def chat_user_flag(chat_obj, user):
    for member in chat_obj.chat_members.all():
        if user.id == member.id:
            return True

    for member in chat_obj.chat_admin.all():
        if user.id == member.id:
            return True


def index(request):
    return render(request, 'chat/index.html', {})


class case_room_auth(APIView):

    def get(self, request, case_id):
        try:
            current_case = case.objects.get(pk=case_id)
            return render(request, 'chat/case_auth.html')
        except:
            return JsonResponse({"ERROR": "Case does not exist"})

    def post(self, request, case_id):
        token_val = request.POST['Token']
        token = Token.objects.get(key=token_val)
        user = token.user
        current_case = case.objects.get(pk=int(case_id))
        if case_user_flag(current_case, user) or case_client_flag(current_case, user):
            return render(request, 'chat/case_room.html', {
                'room_name': case_id,
                'user': user.id
            })
        else:
            return JsonResponse({"ERROR": "Not authorized to enter this chat"})


class new_user_room(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, user_id):
        if user_id < request.user.id:
            tuple1 = (user_id, request.user.id)
        else:
            tuple1 = (request.user.id, user_id)
        new_hash = hash(tuple1)
        print(new_hash)
        new_chat = chat.objects.create(channel_number=str(new_hash))
        new_chat.chat_members.add(request.user)
        new_chat.chat_members.add(User.objects.get(pk=user_id))
        new_chat.save()
        return JsonResponse({"Channel_number": new_hash})


class existing_user_room(APIView):

    def get(self, request, room_name):
        try:
            chat_set = chat.objects.get(channel_number=int(room_name))
            return render(request, 'chat/case_auth.html')
        except:
            return JsonResponse({"ERROR": "Channel does not exist"})

    def post(self, request, room_name):
        flag = 0
        token = Token.objects.get(key=request.POST['Token'])
        current_user = token.user
        current_chat = chat.objects.get(channel_number=room_name)
        print(current_chat.chat_members.all())
        for user in current_chat.chat_members.all():
            if current_user.id == user.id:
                flag = 1
        if flag == 1:
            return render(request, 'chat/channel_room.html', {
                'room_name': room_name,
                'user': current_user.id
            })
        else:
            return JsonResponse({'Message': 'Error Invalid authentication'}, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, room_name):
        try:
            chat_set = chat.objects.get(channel_number=int(room_name))
            for user in chat_set.chat_members.all():
                if request.user.id == user.id:
                    chat_set.delete()
                    return JsonResponse({"Chat": "Deleted"})
            return JsonResponse({"ERROR": "You do not have authority to delete this chat"})
        except:
            return JsonResponse({"ERROR": "Chat does not exist"})


class chat_msg_delete(APIView):
    permission_classes = [IsAuthenticated]

    def delete(self, request, msg_id):
        message_entry = message.objects.get(pk=msg_id)
        for user in message_entry.chat.chat_members.all():
            if request.user == user:
                message_entry.delete()
                return JsonResponse({'Message': 'Deleted'}, status=status.HTTP_200_OK)
        return JsonResponse({'Message': 'Error Invalid authentication'}, status=status.HTTP_400_BAD_REQUEST)


class new_group_room(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        new_chat = chat.objects.create(chat_name=request.data['group_name'])
        new_chat.chat_admin.add(request.user)
        new_chat.save()
        new_hash = hash(str(new_chat.created_at))
        new_chat.channel_number = abs(new_hash)
        new_chat.save()
        return JsonResponse({"Channel_number": abs(new_hash)})


class existing_group_room(APIView):

    def get(self, request, room_name):
        try:
            new_chat = chat.objects.get(channel_number=int(room_name))
            return render(request, 'chat/case_auth.html')
        except:
            return JsonResponse({"ERROR": "Channel does not exist"})

    def post(self, request, room_name):
        token = Token.objects.get(key=request.POST['Token'])
        current_user = token.user
        current_chat = chat.objects.get(channel_number=room_name)
        for user in current_chat.chat_members.all():
            if current_user.id == user.id:
                return render(request, 'chat/group_room.html', {
                    'room_name': room_name,
                    'user': current_user.id
                })
        for user in current_chat.chat_admin.all():
            if current_user.id == user.id:
                return render(request, 'chat/group_room.html', {
                    'room_name': room_name,
                    'user': current_user.id
                })
        return JsonResponse({"ERROR": "Not a member of this group"})


class group_members(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, room_name):
        new_chat = chat.objects.get(channel_number=room_name)
        if chat_user_flag(new_chat, request.user):
            dict2 = {'members': [], 'admins': []}
            chat_member_set = new_chat.chat_members.all()
            for user in chat_member_set:
                profile_set = profile.objects.filter(user=user)
                dict1 = {
                    'id': user.id,
                    'username': user.username,
                    'email': user.email,
                    'image': None,
                    'private': None
                }
                if len(profile_set) != 0:
                    serializer = profile_image_serializer(profile_set[0])
                    dict1['image'] = serializer.data
                    dict1['private'] = profile_set[0].private
                dict2['members'].append(dict1)

            for user in new_chat.chat_admin.all():
                profile_set = profile.objects.filter(user=user)
                dict1 = {
                    'id': user.id,
                    'username': user.username,
                    'email': user.email,
                    'image': None,
                    'private': None
                }
                if len(profile_set) != 0:
                    serializer = profile_image_serializer(profile_set[0])
                    dict1['image'] = serializer.data
                    dict1['private'] = profile_set[0].private
                dict2['admins'].append(dict1)

            return JsonResponse(dict2, status=status.HTTP_200_OK)
        return JsonResponse({'Message': 'Error Unauthorized access'}, status=status.HTTP_400_BAD_REQUEST)

    def post(self, request, room_name):
        new_chat = chat.objects.get(channel_number=room_name)
        for user in new_chat.chat_admin.all():
            if request.user.id == user.id:
                for user_id in request.data['group_member']:
                    user = User.objects.get(pk=user_id)
                    new_chat.chat_members.add(user)
                return JsonResponse({"Chat Members": "Added"}, status=status.HTTP_200_OK)
            return JsonResponse({'Message': 'Error you are not authorized to add members in the group'},
                                status=status.HTTP_400_BAD_REQUEST)
        else:
            return JsonResponse({"ERROR": "No Authorization to add members"}, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, room_name):
        current_chat = chat.objects.get(channel_number=room_name)
        flag = 0

        for chat_entry in request.user.chat_admin.all():
            if chat_entry == current_chat:
                flag = 1
                break

        if request.data['group_member'] == request.user.id or flag == 1:
            for user in current_chat.chat_admin.all():
                if user.id == request.data['group_member']:
                    current_chat.chat_admin.remove(user)
                    current_chat.save()
                    if len(current_chat.chat_admin.all()) == 0:
                        if len(current_chat.chat_members.all()) == 0:
                            current_chat.delete()
                            return JsonResponse({"Chat": "Deleted"}, status=status.HTTP_200_OK)
                        else:
                            current_chat.chat_admin.add(current_chat.chat_members.all()[0])
                            current_chat.chat_members.remove(current_chat.chat_members.all()[0])
                            current_chat.save()
                    return JsonResponse({"Chat": "Left"}, status=status.HTTP_200_OK)

            for user in current_chat.chat_members.all():
                if user.id == request.data['group_member']:
                    current_chat.chat_members.remove(user)
                    current_chat.save()
                    return JsonResponse({'Message': 'Member removed'}, status=status.HTTP_200_OK)

            return JsonResponse({'Message': 'Error group_member not found'}, status=status.HTTP_400_BAD_REQUEST)
        return JsonResponse({'Message': 'Error you are not admin of the case'}, status=status.HTTP_400_BAD_REQUEST)


class group_admin(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, room_name):
        current_chat = chat.objects.get(channel_number=room_name)
        for chat_entry in request.user.chat_admin.all():
            if chat_entry == current_chat:
                for user in current_chat.chat_members.all():
                    if user.id == request.data['admin']:
                        current_chat.chat_members.remove(user)
                        current_chat.chat_admin.add(user)
                        current_chat.save()
                        return JsonResponse({'Message': 'Admin added'}, status=status.HTTP_200_OK)
                    else:
                        return JsonResponse({'Message': 'Error user is not already an admin'},
                                            status=status.HTTP_400_BAD_REQUEST)
            else:
                return JsonResponse({'Message': 'Error you are not admin of the case'},
                                    status=status.HTTP_400_BAD_REQUEST)


class get_case_chat(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, case_id):
        current_case = case.objects.get(pk=case_id)
        current_chat = chat.objects.get(case=current_case)
        f = open('chat/chat_files/case_chat.txt', 'w')
        message_set = current_chat.message_set.all()
        for message_obj in message_set:
            message_string = str(message_obj.created_at) + ' ' + str(message_obj.created_by) + ' ' + message_obj.content
            f.write(message_string + '\n')
        f.close()
