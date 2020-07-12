from django.shortcuts import render, redirect
from django.http import JsonResponse
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from .serializer import *
from django.contrib.auth import authenticate
from rest_framework.authtoken.models import Token
from django.contrib.auth.models import User
from .models import *
from datetime import datetime
from cases.models import case
from user.serializers import *
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


def index(request):
    return render(request, 'chat/index.html', {})


class case_room_auth(APIView):
    permission_classes = [IsAuthenticated]

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
    permission_classes = [IsAuthenticated]

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
        for user in current_chat.chat_members.all():
            if current_user.id == user.id:
                flag = 1
        if flag == 1:
            return render(request, 'chat/channel_room.html', {
                'room_name': room_name,
                'user': current_user.id
            })

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


class new_group_room(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        new_chat = chat.objects.create(chat_name=request.data['group_name'])
        new_chat.chat_admin.add(request.user)
        new_chat.save()
        new_hash = hash(str(new_chat.created_at))
        new_chat.channel_number = new_hash
        new_chat.save()
        return JsonResponse({"Channel_number": new_hash})


class existing_group_room(APIView):
    permission_classes = [IsAuthenticated]

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

    def delete(self, request, room_name):
        try:
            chat_set = chat.objects.get(channel_number=room_name)
            for user in chat_set.chat_admin.all():
                if request.user.id == user.id:
                    chat_set.delete()
                    return JsonResponse({"Chat": "Deleted"})
            return JsonResponse({"ERROR": "You do not have authority to delete this chat"})
        except:
            return JsonResponse({"ERROR": "Chat does not exist"})


class group_members(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, room_name):
        result = []
        new_chat = chat.objects.get(channel_number=room_name)
        admin_set = new_chat.chat_admin.all()
        chat_member_set = new_chat.chat_members.all()
        serializer = UserSerializer(chat_member_set, many=True)
        result.append({"members":serializer.data})
        serializer = UserSerializer(admin_set, many=True)
        result.append({"admin": serializer.data})
        return JsonResponse(result, safe=False)

    def post(self, request, room_name):
        new_chat = chat.objects.get(channel_number=room_name)
        for user in new_chat.chat_admin.all():
            if request.user.id == user.id:
                for user_id in request.data['group_members']:
                    user = User.objects.get(pk=user_id)
                    new_chat.chat_members.add(user)
                    return JsonResponse({"Chat Members": "Added"})
        else:
            return JsonResponse({"ERROR": "No Authorization to add members"})

    def delete(self, request, room_name):
        new_chat = chat.objects.get(chat_name=room_name)
        for user in new_chat.chat_admin.all():
            if request.user.id == user.id:
                for user_id in request.data['group_members']:
                    user = User.objects.get(pk=user_id)
                    new_chat.chat_members.remove(user)
                    return JsonResponse({"Chat Members": "Removed"})
        else:
            return JsonResponse({"ERROR": "No Authorization to remove members"})


class group_admin(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, room_name):
        current_chat = chat.objects.get(channel_number=room_name)
        for admin in current_chat.chat_admin.all():
            if request.user.id == admin.id:
                for new_user in request.data['add_admin']:
                    for user in current_chat.chat_members.all():
                        if new_user == user.id:
                            user_obj = User.objets.get(pk=new_user)
                            current_chat.chat_members.add(user_obj)


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
