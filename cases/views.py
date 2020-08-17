from django.http import JsonResponse
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.parsers import JSONParser, MultiPartParser, FormParser
from rest_framework import status
from .serializers import *
from django.contrib.auth import authenticate
from rest_framework.authtoken.models import Token
from django.contrib.auth.models import User
from rest_framework.decorators import api_view, permission_classes
import pytz
from .models import *
from datetime import datetime, timedelta, time, date
from chat.models import *
from chat.serializer import *
import json
import zipfile
from chat.views import *
from user.models import *
from user.serializers import *
from django.db.models import Q
from case_settings.models import *
import os


def case_user_flag(case_obj, user):
    for member in case_obj.case_members.all():
        if user.id == member.id:  # (flag) check if the user is member of the case
            return True


def case_client_flag(case_obj, user):
    for member in case_obj.case_clients.all():
        if user.id == member.id:  # (flag) check if the user is client of the case
            return True


def task_user_flag(task_obj, user):
    for member in task_obj.task_members.all():
        if user.id == member.id:  # (flag) check if the user is member of the task
            return True


class create_Case(APIView):
    permission_classes = ([IsAuthenticated])

    def post(self, request):
        try:
            if len(case.objects.filter(created_by=request.user)) < user_subscribe.objects.get(user=request.user,
                                                                                              status='current').subscription.case:
                serializer = case_serializer(data=request.data)
                if serializer.is_valid():
                    serializer.validated_data['created_by'] = request.user
                    serializer.validated_data['case_members'] = [request.user]
                    serializer.save()

                    case_all = case.objects.all()
                    chat_obj = chat.objects.create(case=case_all[len(case_all) - 1])
                    chat_obj.chat_members.add(request.user)
                    chat_obj.save()

                    return Response(serializer.data, status=status.HTTP_201_CREATED)
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
            return JsonResponse({"Message": "Case cannot be created, Subscription limit reached"},
                                status=status.HTTP_200_OK)
        except:
            return JsonResponse({"Message": 'Error Invalid Authentication'}, status=status.HTTP_400_BAD_REQUEST)


class show_cases(APIView):
    permission_classes([IsAuthenticated])

    def get(self, request):
        user = User.objects.get(pk=request.user.id)
        case_set_member = user.case_members.all()
        case_set_client = user.case_clients.all()

        if len(case_set_member) != 0 or len(case_set_client) != 0:
            serializer = case_show_serializer(case_set_member, many=True)
            obj = case_show_serializer()
            final = obj.show(serializer.data)
            result = final
            serializer = case_show_serializer(case_set_client, many=True)
            final = obj.show(serializer.data)
            result = result + final
            return JsonResponse(result, safe=False, status=status.HTTP_200_OK)
        else:
            return JsonResponse([], safe=False, status=status.HTTP_200_OK)


class show_case(APIView):
    permission_classes = ([IsAuthenticated])

    def get(self, request, case_id, format='json'):
        try:
            list1 = []
            queryset = case.objects.filter(pk=case_id)
            serializer = case_show_serializer(queryset, many=True)
            obj = case_show_serializer()
            final = obj.show(serializer.data)
            current_case = case.objects.get(pk=case_id)
            if case_client_flag(current_case, request.user) or case_user_flag(current_case, request.user):
                task_set = current_case.task_set.all()
                for task_element in task_set:
                    timer_set = timer.objects.filter(task=task_element)
                    dict1 = {
                        'id': task_element.id, 'name': task_element.task_name,
                        'created_by': task_element.created_by.username,
                        'billing_type': task_element.billing_type,
                        'invoice_type': task_element.invoice_type,
                        'cost': task_element.cost,
                        'due_date': task_element.due_date,
                        'created_at': task_element.created_at,
                        'timer': []
                    }
                    if len(timer_set) != 0:
                        serializer = timer_serializer(timer_set, many=True)
                        dict1['timer'] = serializer.data

                    try:
                        invoice_obj = task_invoice.objects.get(task=task_element)
                        dict1['invoice'] = invoice_obj.created_at
                        payment_set = invoice_payment.objects.filter(invoice=invoice_obj)
                        if payment_set[len(payment_set) - 1].status:
                            dict1['invoice_paid'] = True
                        else:
                            dict1['invoice_paid'] = False

                    except:
                        dict1['invoice'] = None
                        dict1['invoice_paid'] = None

                    list1.append(dict1)
                final.append({"tasks": list1})
                return Response(final, status=status.HTTP_200_OK)
            return JsonResponse({"Message": "Error Unauthorized Access"}, status=status.HTTP_400_BAD_REQUEST)
        except:
            return JsonResponse({"Message": "Error Invalid Case"}, status=status.HTTP_400_BAD_REQUEST)

    def put(self, request, case_id):
        try:
            current_case = case.objects.get(pk=case_id)
            if case_user_flag(current_case, request.user):
                if current_case.completed is None:
                    current_case.case_name = request.data.get('case_name', current_case.case_name)
                    current_case.case_type = request.data.get('case_type', current_case.case_type)
                    current_case.description = request.data.get('description', current_case.description)
                    current_case.save()
                    serializer = case_serializer(current_case)
                    return Response(serializer.data, status=status.HTTP_200_OK)
                return JsonResponse({'Message': 'Error Case is completed'}, status=status.HTTP_400_BAD_REQUEST)
            return JsonResponse({"Message": "Error Unauthorized Access"}, status=status.HTTP_400_BAD_REQUEST)
        except:
            return JsonResponse({"Message": "Error Invalid Case"}, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, case_id, format=None):
        try:
            current_case = case.objects.get(pk=case_id)
            if request.user.id == current_case.created_by.id and current_case.completed is None:
                current_case.delete()
                return JsonResponse({"Case": "Deleted"}, status=status.HTTP_200_OK)
            return JsonResponse({"Message": "Error Unauthorized Access"}, status=status.HTTP_400_BAD_REQUEST)
        except:
            return JsonResponse({"Message": "Error Invalid Case"}, status=status.HTTP_400_BAD_REQUEST)


class clients(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        final = []
        result = set()
        case_set = request.user.case_members.all()
        for case_obj in case_set:
            for client in case_obj.case_clients.all():
                result.add(client)

        result = list(result)
        for client in result:
            profile_entry = profile.objects.filter(user=client)
            client_cases = client.case_clients.all()
            common_cases = client_cases.intersection(case_set)
            dict1 = {
                'client': {'id': client.id, 'username': client.username, 'email': client.email, 'image': None,
                           'private': None},
                'cases': []
            }
            if len(profile_entry) != 0:
                image_serializer = profile_image_serializer(profile_entry, many=True)
                dict1['client']['image'] = image_serializer.data[0]
                dict1['client']['private'] = profile_entry[0].private

            for element in common_cases:
                dict2 = {'id': element.id, 'name': element.case_name}
                dict1['cases'].append(dict2)
            final.append(dict1)

        return JsonResponse(final, safe=False, status=status.HTTP_200_OK)

    def post(self, request):
        username_results = User.objects.filter(Q(username__icontains=request.data.get('info', '')))
        result = set()
        case_set = request.user.case_members.all()
        for case_obj in case_set:
            for member in case_obj.case_clients.all():
                result.add(member)

        final = set(username_results).intersection(result)
        result = []
        for element in final:
            dict1 = {'id': element.id, 'username': element.username, 'email': element.email}
            result.append(dict1)

        return JsonResponse(result, safe=False, status=status.HTTP_200_OK)


class members(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        final = []
        result = set()
        case_set = request.user.case_members.all()
        for case_obj in case_set:
            for member in case_obj.case_members.all():
                result.add(member)

        result = list(result)
        for member in result:
            profile_entry = profile.objects.filter(user=member)
            member_cases = member.case_members.all()
            common_cases = member_cases.intersection(case_set)
            dict1 = {
                'member': {'id': member.id, 'username': member.username, 'email': member.email, 'image': None,
                           'private': None},
                'cases': []
            }
            if len(profile_entry) != 0:
                image_serializer = profile_image_serializer(profile_entry, many=True)
                dict1['member']['image'] = image_serializer.data[0]
                dict1['member']['private'] = profile_entry[0].private

            for element in common_cases:
                dict2 = {'id': element.id, 'name': element.case_name}
                dict1['cases'].append(dict2)
            final.append(dict1)

        return JsonResponse(final, safe=False, status=status.HTTP_200_OK)

    def post(self, request):
        username_results = User.objects.filter(Q(username__icontains=request.data.get('info', '')))
        result = set()
        case_set = request.user.case_members.all()
        for case_obj in case_set:
            for member in case_obj.case_members.all():
                result.add(member)

        final = set(username_results).intersection(result)
        result = []
        for element in final:
            dict1 = {'id': element.id, 'username': element.username, 'email': element.email}
            result.append(dict1)

        return JsonResponse(result, safe=False, status=status.HTTP_200_OK)


class search_case(APIView):

    def post(self, request):
        result = []
        case_set_member = request.user.case_members.all()
        case_set_client = request.user.case_clients.all()

        case_name_results = case.objects.filter(Q(case_name__icontains=request.data.get('info', '')))

        total = case_set_member.union(case_set_client)
        case_name_results = case_name_results.intersection(total)
        for element in case_name_results:
            dict1 = {'id': element.id, 'name': element.case_name}
            result.append(dict1)
        return JsonResponse(result[:10], safe=False, status=status.HTTP_200_OK)


class case_assign_members(APIView):
    permission_classes = ([IsAuthenticated])

    def post(self, request, case_id, format='json'):
        try:
            current_case = case.objects.get(pk=case_id)

            if len(current_case.case_members.all()) < user_subscribe.objects.get(
                    user=request.user, status='current').subscription.case_member:
                if case_user_flag(current_case, request.user) and current_case.completed is None:
                    already_member = []
                    already_client = []
                    new_users = []

                    for member_id in request.data['case_members']:
                        user = User.objects.get(pk=member_id)
                        existing_member = current_case.case_members.filter(pk=user.id)
                        existing_client = current_case.case_clients.filter(pk=user.id)

                        if len(existing_member) != 0:
                            already_member.append(member_id)
                        elif len(existing_client) != 0:
                            already_client.append(member_id)
                        else:
                            invite_user = invite.objects.create(case=current_case, sent_to=user, position='case_member',
                                                                sent_from=request.user)
                            new_users.append(user.id)
                            invite_user.save()

                    if len(already_member) == 0 and len(already_client) == 0:
                        return JsonResponse({"New invite sent": new_users}, status=status.HTTP_200_OK)
                    elif len(already_member) != 0 or len(already_client) != 0:
                        return JsonResponse(
                            {"Users already members": already_member, "Users already clients": already_client,
                             "New invites sent": new_users}, status=status.HTTP_200_OK)
                else:
                    return JsonResponse({"Message": "Error Unauthorized Access"}, status=status.HTTP_400_BAD_REQUEST)
            else:
                return JsonResponse({"Message": "Member cannot be added, Subscription limit reached"},
                                    status=status.HTTP_200_OK)
        except:
            return JsonResponse({"Message": "Error Invalid Case"}, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, case_id):
        try:
            current_case = case.objects.get(pk=case_id)
            current_chat = chat.objects.get(case=current_case)

            if case_user_flag(current_case, request.user) and current_case.completed is None:
                for member in request.data['case_members']:
                    user = User.objects.get(pk=member)
                    existing_member = current_case.case_members.filter(username=user.username)
                    if user == current_case.created_by:
                        if request.user == current_case.created_by:
                            current_case.case_members.remove(user)
                            current_chat.chat_members.remove(user)
                            if len(current_case.case_members.all()) == 0:
                                current_case.delete()
                                return JsonResponse({"Case": "Closed"}, status=status.HTTP_200_OK)
                            else:
                                current_case.created_by = current_case.case_members.all()[0]
                                current_case.save()
                        else:
                            return JsonResponse({'Message': 'You cannot remove the admin'},
                                                status=status.HTTP_400_BAD_REQUEST)
                    if len(existing_member) == 0:
                        return JsonResponse({"Message": "Error Requested User is not currently member of this case"},
                                            status=status.HTTP_400_BAD_REQUEST)
                    current_case.case_members.remove(user)
                    current_chat.chat_members.remove(user)
                    current_case.save()
                    current_chat.save()
                    for element in user.task_members.all():
                        element.task_members.remove(user)
                        element.save()

                return JsonResponse({"Case": "Members removed"}, status=status.HTTP_200_OK)
            else:
                return JsonResponse({"Message": "Error Unauthorized Access"}, status=status.HTTP_400_BAD_REQUEST)
        except:
            return JsonResponse({"Message": "Error Invalid Case"}, status=status.HTTP_400_BAD_REQUEST)


class case_assign_clients(APIView):
    permission_classes = ([IsAuthenticated])

    def post(self, request, case_id, format='json'):
        try:
            current_case = case.objects.get(pk=case_id)

            if len(current_case.case_members.all()) < user_subscribe.objects.get(
                    user=request.user, status='current').subscription.case_clients:
                if case_user_flag(current_case, request.user) and current_case.completed is None:
                    already_member = []
                    already_client = []
                    new_users = []

                    for client_id in request.data['case_clients']:
                        user = User.objects.get(pk=client_id)
                        existing_member = current_case.case_members.filter(pk=user.id)
                        existing_client = current_case.case_clients.filter(pk=user.id)

                        if len(existing_member) != 0:
                            already_member.append(client_id)
                        elif len(existing_client) != 0:
                            already_client.append(client_id)
                        else:
                            invite_user = invite.objects.create(case=current_case, sent_to=user, position='case_client',
                                                                sent_from=request.user)
                            new_users.append(user.id)
                            invite_user.save()

                    if len(already_member) == 0 and len(already_client) == 0:
                        return JsonResponse({"New invite sent": new_users}, status=status.HTTP_200_OK)
                    elif len(already_member) != 0 or len(already_client) != 0:
                        return JsonResponse(
                            {"Users already members": already_member, "Users already clients": already_client,
                             "New invites sent": new_users}, status=status.HTTP_200_OK)
                else:
                    return JsonResponse({"Message": "Error Unauthorized Access"}, status=status.HTTP_400_BAD_REQUEST)
            else:
                return JsonResponse({"Message": "Client cannot be added, Subscription limit reached"},
                                    status=status.HTTP_200_OK)
        except:
            return JsonResponse({"Message": "Error Invalid Case"}, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, case_id):
        try:
            current_case = case.objects.get(pk=case_id)
            current_chat = chat.objects.get(case=current_case)

            if case_user_flag(current_case, request.user) and current_case.completed is None:
                for member in request.data['case_clients']:
                    user = User.objects.get(pk=member)
                    current_case.case_clients.remove(user)
                    current_chat.chat_members.remove(user)
                    current_case.save()
                    current_chat.save()
                    for element in user.task_members.all():
                        element.task_members.remove(user)
                        element.save()

                return JsonResponse({"clients": "Removed"}, status=status.HTTP_200_OK)
            else:
                return JsonResponse({"Message": "Error Unauthorized Access"}, status=status.HTTP_400_BAD_REQUEST)
        except:
            return JsonResponse({"Message": "Error Invalid Case"}, status=status.HTTP_400_BAD_REQUEST)


class case_admin(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, case_id, user_id):
        current_case = case.objects.get(pk=case_id)
        user = User.objects.get(pk=user_id)

        if request.user == current_case.created_by and current_case.completed is None:
            try:
                case_member_entry = current_case.case_members.get(username=user.username)
                current_case.created_by = user
                current_case.save()
                return JsonResponse({'Case Admin': 'Changed'}, status=status.HTTP_200_OK)
            except:
                return JsonResponse({'Message': 'Error user does not belong to case member list'},
                                    status=status.HTTP_400_BAD_REQUEST)
        return JsonResponse({'Message': 'Error Only the case admin can change admins'},
                            status=status.HTTP_400_BAD_REQUEST)


class add_task(APIView):
    permission_classes = ([IsAuthenticated])

    def post(self, request, case_id, foramt='json'):
        try:
            current_case = case.objects.get(pk=case_id)

            if len(task.objects.filter(task_case=current_case)) < user_subscribe.objects.get(
                    user=request.user, status='current').subscription.task:
                if case_user_flag(current_case, request.user) and current_case.completed is None:
                    serializer = task_create_serializer(data=request.data)
                    if serializer.is_valid():
                        serializer.validated_data['task_case'] = current_case  # create task
                        serializer.validated_data['created_by'] = request.user
                        serializer.validated_data['task_members'] = [request.user]
                        serializer.validated_data['billing_type'] = request.data.get('billing_type', 'non billing')

                        if serializer.validated_data['billing_type'] == 'billing':
                            if request.data.get('invoice_type') is None:
                                return Response(
                                    {'Message': 'Error invoice_type cannot be null when billing_type is billing'},
                                    status=status.HTTP_400_BAD_REQUEST)
                            if request.data.get('cost', 0) == 0:
                                return Response({'Message': 'Error cost cannot be 0 when billing_type is billing'},
                                                status=status.HTTP_400_BAD_REQUEST)
                        else:
                            if request.data.get('cost', 0) != 0:
                                return Response(
                                    {'Message': 'Error cost has to be zero when billing_type is non billing'},
                                    status=status.HTTP_400_BAD_REQUEST)
                            if request.data.get('invoice_type') is not None:
                                return Response(
                                    {'Message': 'Error invoice_type has to be null when billing_type is non billing'},
                                    status=status.HTTP_400_BAD_REQUEST)
                        serializer.save()

                        new_task_set = task.objects.all()
                        new_task = new_task_set[len(new_task_set) - 1]
                        new_activity = task_activity.objects.create(task=new_task, user=request.user,
                                                                    action="created task")  # activity
                        new_activity.save()

                        return Response(serializer.data, status=status.HTTP_201_CREATED)
                    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
                else:
                    return JsonResponse({"Message": "Error Unauthorized Access"}, status=status.HTTP_400_BAD_REQUEST)
            else:
                return JsonResponse({"Message": "Task cannot be added, Subscription limit reached"},
                                    status=status.HTTP_200_OK)
        except:
            return JsonResponse({"Message": "Error Invalid Case"}, status=status.HTTP_400_BAD_REQUEST)


class add_task_members(APIView):
    permission_classes = ([IsAuthenticated])

    def post(self, request, task_id):
        current_task = task.objects.get(pk=task_id)
        prob = []
        added_users = []
        already_member = []
        flag = 0
        if (case_user_flag(current_task.task_case, request.user) or case_client_flag(current_task.task_case,
                                                                                     request.user)) and current_task.completed is None:
            member_set = request.data['task_members']
            for member in member_set:
                user = User.objects.get(pk=member)
                if case_user_flag(current_task.task_case, user) or case_client_flag(current_task.task_case, user):
                    if flag == 0:
                        current_task.task_members.add(user)
                        current_task.save()

                        new_activity = task_activity.objects.create(task=current_task, user=request.user,
                                                                    action="updated task members")  # activity
                        new_activity.save()
                        added_users.append(member)
                        break
                else:
                    prob.append(member)
                    break
            if len(prob) == 0:
                return JsonResponse({"Task_Members": "Added"}, status=status.HTTP_200_OK)
            else:
                return JsonResponse(
                    {'Message': {
                        "Error Given users are not in the case and cannot be added as task members": prob,
                        'new users added': added_users}}, status=status.HTTP_200_OK)
        else:
            return JsonResponse({"ERROR": "You are not authorized to add member to this task"},
                                status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, task_id):
        current_task = task.objects.get(pk=task_id)
        if (case_user_flag(current_task.task_case, request.user) or case_client_flag(current_task.task_case,
                                                                                     request.user)) and current_task.completed is None:
            for member_id in request.data['task_members']:
                user = User.objects.get(pk=member_id)
                if user == current_task.created_by:
                    if request.user == current_task.created_by:
                        current_task.task_members.remove(user)
                        current_task.save()
                        break
                    else:
                        return JsonResponse({'Message': 'Error you cannot remove creator of the task'},
                                            status=status.HTTP_400_BAD_REQUEST)
                current_task.task_members.remove(user)
                current_task.save()
                break
            return JsonResponse({"task_members": "Deleted"}, status=status.HTTP_200_OK)
        else:
            return JsonResponse({"Message": "Error You are not a member of this case"},
                                status=status.HTTP_400_BAD_REQUEST)


class show_task_complete(APIView):
    permission_classes = ([IsAuthenticated])

    def task_members_username(self, validated_data):
        result = []
        for user_id in validated_data['task_members']:
            user = User.objects.get(pk=user_id)
            dict1 = {'id': user.id, 'username': user.username, 'email': user.email, 'private': None}
            profile_data = profile.objects.filter(user=user)
            if len(profile_data) == 0:
                dict1['image'] = None
            else:
                serializer = profile_image_serializer(profile_data, many=True)
                dict1['image'] = serializer.data[0]
                dict1['private'] = profile_data[0].private
            result.append(dict1)
        return result

    def get(self, request, task_id):
        current_task = task.objects.get(pk=task_id)
        if case_user_flag(current_task.task_case, request.user) or case_client_flag(current_task.task_case,
                                                                                    request.user):
            serializer = task_show_serializer(current_task)
            obj = show_task_complete()
            final = serializer.data
            final['task_members'] = obj.task_members_username(serializer.data)

            #       START OF CASE SECTION

            final['task_case'] = {
                'id': current_task.task_case.id,
                'name': current_task.task_case.case_name,
                'created_at': current_task.task_case.created_at
            }

            final['created_at'] = current_task.created_at
            final['updated_at'] = current_task.updated_at

            final['created_by'] = {
                'id': current_task.created_by.id,
                'username': current_task.created_by.username,
                'email': current_task.created_by.email,
                'image': None, 'private': None
            }
            profile_info = profile.objects.filter(user=current_task.created_by)
            if len(profile_info) != 0:
                image_serializer = profile_image_serializer(profile_info, many=True)
                final['created_by']['image'] = image_serializer.data[0]
                final['created_by']['private'] = profile_info[0].private

            #       START OF COMMENT SECTION

            task_comments = comments.objects.filter(task=current_task).order_by('-created_at')
            result = []
            for item in task_comments:
                user = item.comment_user
                user_profile = profile.objects.filter(user=user)
                image_serializer = profile_image_serializer(user_profile, many=True)

                if item.created_at.strftime('%d-%m-%Y %H:%M:%S') != item.updated_at.strftime('%d-%m-%Y %H:%M:%S'):
                    edited = True
                else:
                    edited = False

                if len(user_profile) == 0:
                    dict1 = {'id': item.id, 'comment': item.comment,
                             'user': {'id': user.id, 'username': user.username, 'image': None, 'private': None},
                             'created_at': item.created_at, 'edited': edited,
                             'updated_at': item.updated_at}
                    result.append(dict1)
                else:
                    dict1 = {'id': item.id, 'comment': item.comment,
                             'user': {'id': user.id,
                                      'username': user.username,
                                      'email': user.email,
                                      'image': image_serializer.data[0],
                                      'private': user_profile[0].private
                                      },
                             'created_at': item.created_at, 'edited': edited,
                             'updated_at': item.updated_at}
                    result.append(dict1)

            final['comments'] = result

            #       END OF COMMENT SECTION

            #       START OF CHECKLIST SECTION

            checklist_set = checklist.objects.filter(task=current_task)
            result = []
            for item in checklist_set:
                dict1 = {
                    'id': item.id, 'checklist_name': item.checklist_name, 'complete': item.complete,
                    'checklist_items': [],
                    'created_at': item.created_at,
                    'updated_at': item.updated_at
                }
                checklist_item_set = checklist_items.objects.filter(checklist=item)

                for entry in checklist_item_set:
                    dict2 = {
                        'id': entry.id, 'item': entry.item, 'complete': entry.complete,
                        'created_at': entry.created_at,
                        'updated_at': entry.updated_at
                    }
                    dict1['checklist_items'].append(dict2)
                result.append(dict1)

            final['checklist'] = result

            #       END OF CHECKLIST SECTION

            #       START OF LABEL SECTION

            label_set = task_labels.objects.filter(task=current_task)
            if len(label_set) != 0:
                serializer4 = task_label_serializer(label_set, many=True)
                final['label'] = serializer4.data
            else:
                final['label'] = []

            #       END OF LABEL SECTION

            timer_set = timer.objects.filter(task=current_task)
            serializer = timer_serializer(timer_set, many=True)
            final['timer'] = serializer.data

            final['completed'] = current_task.completed

            #       START OF TASK INVOICE SECTION

            try:
                invoice_obj = task_invoice.objects.get(task=current_task)
                final['invoice'] = invoice_obj.created_at
                payment_set = invoice_payment.objects.filter(invoice=invoice_obj)
                if payment_set[len(payment_set) - 1].status:
                    final['invoice_paid'] = True
                else:
                    final['invoice_paid'] = False

            except:
                final['invoice'] = None
                final['invoice_paid'] = None

            return JsonResponse(final, safe=False, status=status.HTTP_200_OK)
        else:
            return JsonResponse({"Message": "Error You are not a member of this case"}, status=status.HTTP_200_OK)

    def put(self, request, task_id):
        current_task = task.objects.get(pk=task_id)
        if case_user_flag(current_task.task_case, request.user) and current_task.completed is None:
            current_task.task_name = request.data.get("task_name", current_task.task_name)
            current_task.details = request.data.get("details", current_task.details)
            current_task.billing_type = request.data.get("billing_type", current_task.billing_type)
            current_task.invoice_type = request.data.get('invoice_type', current_task.invoice_type)

            if request.data.get('due_date') is not None:
                try:
                    datetime_object = datetime.strptime(request.data['due_date'], '%Y-%m-%d')
                except:
                    return JsonResponse({'Message': 'Error Due date must be in format %Y-%m-%d'},
                                        status=status.HTTP_400_BAD_REQUEST)  # adding due_date
                if datetime_object.date() > date.today():
                    current_task.due_date = datetime_object.date()
                else:
                    return JsonResponse({'Message': 'Error due_date cannot be behind current date'},
                                        status=status.HTTP_400_BAD_REQUEST)

            if current_task.billing_type == 'billing':
                if current_task.invoice_type is not None:
                    current_task.cost = request.data.get('cost', current_task.cost)
                else:
                    return JsonResponse({'Message': 'Error Invoice_type cannot be null when billing_type is billing'},
                                        status=status.HTTP_400_BAD_REQUEST)  # adding Billing Response
                if current_task.cost == 0:
                    return Response({'Message': 'Error Cost cannot be 0 with billing_type as Billing'},
                                    status=status.HTTP_400_BAD_REQUEST)
            if current_task.billing_type == 'non billing':
                if request.data.get('cost', 0) != 0:
                    return Response(
                        {'Message': 'Error cost has to be zero when billing_type is non billing'},
                        status=status.HTTP_400_BAD_REQUEST)
                if request.data.get('invoice_type') is not None:
                    return Response(
                        {'Message': 'Error invoice_type has to be null when billing_type is non billing'},
                        status=status.HTTP_400_BAD_REQUEST)
            current_task.save()

            new_activity = task_activity.objects.create(task=current_task, user=request.user,
                                                        action='updated task')
            new_activity.save()

            serializer = task_create_serializer(current_task)
            return Response(serializer.data, status=status.HTTP_200_OK)
        else:
            return JsonResponse({"ERROR": "You are not a member of this case"}, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, task_id):
        current_task = task.objects.get(pk=task_id)
        if case_user_flag(current_task.task_case, request.user):
            current_task.delete()
            return JsonResponse({"task": "deleted"}, status=status.HTTP_200_OK)
        else:
            return JsonResponse({"ERROR": "You are not a member of this case"}, status=status.HTTP_400_BAD_REQUEST)


class today_tasks(APIView):
    permission_classes = [IsAuthenticated]

    def display_today_tasks(self, task_element, result, serializer):
        dict1 = {
            'task': {
                'id': task_element.id,
                'name': task_element.task_name,
                'created_at': task_element.created_at,
                'billing_type': task_element.billing_type,
                'members': [],
                'admin': {'id': task_element.created_by.id,
                          'username': task_element.created_by.username,
                          'email': task_element.created_by.email,
                          'image': None,
                          'private': None
                          },
                'due_date': task_element.due_date,
                'details': task_element.details,
                'invoice_type': task_element.invoice_type,
                'cost': task_element.cost,
            },
            'case': {
                'id': task_element.task_case.id,
                'name': task_element.task_case.case_name,
                'case_type': task_element.task_case.case_type
            },
            'timer': serializer.data
        }

        profile_info = profile.objects.filter(user=task_element.created_by)
        image_serializer = profile_image_serializer(profile_info, many=True)
        if len(profile_info) != 0:
            dict1['task']['admin']['image'] = image_serializer.data[0]
            dict1['task']['admin']['private'] = profile_info[0].private

        for user in task_element.task_members.all():
            profile_info = profile.objects.filter(user=user)
            image_serializer = profile_image_serializer(profile_info, many=True)
            if len(profile_info) == 0:
                dict2 = {'id': user.id, 'username': user.username, 'email': user.email, 'image': None, 'private': None}
            else:
                dict2 = {'id': user.id, 'username': user.username, 'email': user.email,
                         'image': image_serializer.data[0],
                         'private': profile_info[0].private}
            dict1['task']['members'].append(dict2)
        result.append(dict1)
        return result

    def get(self, request):
        case_set = request.user.case_members.all()
        obj = today_tasks()
        result = []
        for case_element in case_set:
            task_set = task.objects.filter(task_case=case_element)
            for task_element in task_set:
                if task_element.due_date is not None:
                    timer_set = timer.objects.filter(task=task_element)
                    serializer = timer_serializer(timer_set, many=True)
                    if date.today() == (task_element.due_date - timedelta(days=1)):
                        result = obj.display_today_tasks(task_element, result, serializer)

        return JsonResponse(result, safe=False, status=status.HTTP_200_OK)


class show_active_tasks(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        case_set = request.user.case_members.all()
        obj = today_tasks()
        result = []
        for case_element in case_set:
            task_set = task.objects.filter(task_case=case_element)
            for task_element in task_set:
                dict1 = {}
                timer_set = timer.objects.filter(task=task_element)
                serializer = timer_serializer(timer_set, many=True)
                if len(timer_set) != 0:
                    if timer_set[len(timer_set) - 1].status != 'end':
                        result = obj.display_today_tasks(task_element, result, serializer)
        return JsonResponse(result, safe=False, status=status.HTTP_200_OK)


class search_tasks(APIView):

    def check(self, final, case_set_client, case_set_member, result):
        for element in final:
            dict1 = {'id': element.id, 'name': element.task_name}
            for case_element in case_set_client:
                if element.task_case == case_element:
                    result.append(dict1)
            for case_element in case_set_member:
                if element.task_case == case_element:
                    result.append(dict1)
        return result

    def post(self, request):
        list1 = []
        result = []
        case_set_member = request.user.case_members.all()
        case_set_client = request.user.case_clients.all()

        if len(request.data['info']) >= 3:
            task_name_results = task.objects.filter(Q(task_name__icontains=request.data.get('info', '')))
            task_label_results = task_labels.objects.filter(Q(label__icontains=request.data.get('info', '')))

            for label in task_label_results:
                list1.append(label.task)

            obj = search_tasks()
            result = obj.check(task_name_results, case_set_client, case_set_member, result)
            result = obj.check(list1, case_set_client, case_set_member, result)

            return JsonResponse(result, safe=False, status=status.HTTP_200_OK)
        return Response({}, status=status.HTTP_200_OK)


class add_task_comment(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, task_id):
        current_task = task.objects.get(pk=task_id)
        result = []
        if case_user_flag(current_task.task_case, request.user) or case_client_flag(current_task.task_case,
                                                                                    request.user):
            task_comments = comments.objects.filter(task=current_task).order_by('-created_at')
            for item in task_comments:
                user = item.comment_user
                user_profile = profile.objects.filter(user=user)
                image_serializer = profile_image_serializer(user_profile, many=True)

                if item.created_at.strftime('%d-%m-%Y %H:%M:%S') != item.updated_at.strftime('%d-%m-%Y %H:%M:%S'):
                    edited = True
                else:
                    edited = False

                if len(user_profile) == 0:
                    dict1 = {'id': item.id, 'comment': item.comment,
                             'user': {'id': user.id,
                                      'username': user.username,
                                      'email': user.email,
                                      'image': None,
                                      'private': None
                                      },
                             'created_at': item.created_at, 'edited': edited,
                             'updated_at': item.updated_at}
                    result.append(dict1)
                else:
                    dict1 = {'id': item.id, 'comment': item.comment,
                             'user': {'id': user.id,
                                      'username': user.username,
                                      'email': user.email,
                                      'image': image_serializer.data[0],
                                      'private': user_profile[0].private
                                      },
                             'created_at': item.created_at, 'edited': edited,
                             'updated_at': item.updated_at}
                    result.append(dict1)
            return Response(result, status=status.HTTP_200_OK)
        else:
            return JsonResponse({"ERROR": "You are not a member of this case"}, status=status.HTTP_400_BAD_REQUEST)

    def post(self, request, task_id):
        current_task = task.objects.get(pk=task_id)
        if (case_user_flag(current_task.task_case, request.user) or case_client_flag(current_task.task_case,
                                                                                     request.user)) and current_task.completed is None:
            new_comment = comments.objects.create(task=current_task, comment=request.data['comment'],
                                                  comment_user=request.user)
            new_comment.save()

            new_activity = task_activity.objects.create(task=current_task, user=request.user, action='added comment')
            new_activity.save()

            return JsonResponse({"comment": "added"})
        else:
            return JsonResponse({"ERROR": "You are not a member of this case"}, status=status.HTTP_400_BAD_REQUEST)


class edit_task_comment(APIView):
    permission_classes = ([IsAuthenticated])

    def put(self, request, comment_id):
        current_comment = comments.objects.get(pk=comment_id)
        if request.user.id == current_comment.comment_user.id and current_comment.task.completed is None:
            current_comment.comment = request.data['comment']
            current_comment.save()

            new_activity = task_activity.objects.create(task=current_comment.task, user=request.user,
                                                        action='updated comment')
            new_activity.save()

            return JsonResponse({"comment": "Updated"})
        else:
            return JsonResponse({"ERROR": "You are did not create this comment"})

    def delete(self, request, comment_id):
        current_comment = comments.objects.get(pk=comment_id)
        if request.user.id == current_comment.comment_user.id and current_comment.task.completed is None:
            current_comment.delete()
            return JsonResponse({"comment": "deleted"})
        else:
            return JsonResponse({"ERROR": "You did not create this comment"}, status=status.HTTP_400_BAD_REQUEST)


class add_task_checklist(APIView):
    permission_classes = ([IsAuthenticated])

    def get(self, request, task_id):
        current_task = task.objects.get(pk=task_id)
        result = []
        if case_user_flag(current_task.task_case, request.user) or case_client_flag(current_task.task_case,
                                                                                    request.user):
            checklist_set = checklist.objects.filter(task=current_task)
            for item in checklist_set:
                dict1 = {
                    'id': item.id, 'checklist_name': item.checklist_name, 'complete': item.complete,
                    'checklist_items': [],
                    'created_at': item.created_at,
                    'updated_at': item.updated_at
                }
                checklist_item_set = checklist_items.objects.filter(checklist=item)

                for entry in checklist_item_set:
                    dict2 = {
                        'id': entry.id, 'item': entry.item, 'complete': entry.complete,
                        'created_at': entry.created_at,
                        'updated_at': entry.updated_at
                    }
                    dict1['checklist_items'].append(dict2)

                result.append(dict1)

            return JsonResponse(result, safe=False, status=status.HTTP_200_OK)
        else:
            return JsonResponse({"ERROR": "You are not a member of this case"}, status=status.HTTP_400_BAD_REQUEST)

    def post(self, request, task_id):
        current_task = task.objects.get(pk=task_id)
        if case_user_flag(current_task.task_case, request.user) and current_task.completed is None:
            new_checklist = checklist.objects.create(task=current_task, checklist_name=request.data['checklist_name'],
                                                     created_by=request.user)
            new_checklist.save()

            new_activity = task_activity.objects.create(task=current_task, user=request.user, action='added checklist',
                                                        target=request.data['checklist_name'])
            new_activity.save()

            return JsonResponse({"Checklist": "Created"}, status=status.HTTP_200_OK)
        else:
            return JsonResponse({"Message": "Error You are not member of this case"},
                                status=status.HTTP_400_BAD_REQUEST)


class edit_task_checklist(APIView):
    permission_classes = ([IsAuthenticated])

    def put(self, request, checklist_id):
        current_checklist = checklist.objects.get(pk=checklist_id)
        if case_user_flag(current_checklist.task.task_case, request.user) and current_task.completed is None:
            current_checklist.checklist_name = request.data['checklist_name']
            current_checklist.save()

            new_activity = task_activity.objects.create(task=current_checklist.task, user=request.user,
                                                        action='updated checklist',
                                                        target=request.data['checklist_name'])
            new_activity.save()

            return JsonResponse({"Checklist": "Updated"}, status=status.HTTP_200_OK)
        else:
            return JsonResponse({"Message": "Erro you are not a member of this case"},
                                status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, checklist_id):
        current_checklist = checklist.objects.get(pk=checklist_id)
        if case_user_flag(current_checklist.task.task_case, request.user) and current_task.completed is None:
            current_checklist.delete()
            return JsonResponse({"Checklist": "Deleted"}, status=status.HTTP_200_OK)
        else:
            return JsonResponse({"Message": "Error you are not a member of this case"},
                                status=status.HTTP_400_BAD_REQUEST)


class add_task_checklist_items(APIView):
    permission_classes = ([IsAuthenticated])

    def get(self, request, checklist_id):
        current_checklist = checklist.objects.get(pk=checklist_id)
        if case_user_flag(current_checklist.task.task_case, request.user) or case_client_flag(
                current_checklist.task.task_case,
                request.user):
            checklist_items_set = checklist_items.objects.filter(checklist=current_checklist)
            result = []
            for entry in checklist_items_set:
                dict1 = {'id': entry.id, 'item': entry.item, 'complete': entry.complete,
                         'created_at': entry.created_at,
                         'updated_at': entry.updated_at}
                result.append(dict1)

            return JsonResponse(result, safe=False, status=status.HTTP_200_OK)
        return JsonResponse({'Message': 'Error Invalid Authentication'}, status=status.HTTP_400_BAD_REQUEST)

    def post(self, request, checklist_id):
        current_checklist = checklist.objects.get(pk=checklist_id)
        if case_user_flag(current_checklist.task.task_case, request.user) and current_checklist.task.completed is None:
            new_item = checklist_items.objects.create(checklist=current_checklist, item=request.data['item'])
            new_item.save()

            new_activity = task_activity.objects.create(task=current_checklist.task, user=request.user,
                                                        action='added checklist item', target=request.data['item'])
            new_activity.save()

            return JsonResponse({"Checklist": "Item_added"}, status=status.HTTP_200_OK)
        else:
            return JsonResponse({"Message": "Error you are not a member of this case"},
                                status=status.HTTP_400_BAD_REQUEST)


class edit_checklist_items(APIView):
    permission_classes = ([IsAuthenticated])

    def put(self, request, checklist_item_id):
        current_checklist_item = checklist_items.objects.get(pk=checklist_item_id)
        if case_user_flag(current_checklist_item.checklist.task.task_case,
                          request.user) and current_checklist_item.checklist.task.completed is None:
            current_checklist_item.item = request.data.get('item', current_checklist_item.item)
            current_checklist_item.complete = request.data.get('complete', current_checklist_item.complete)
            current_checklist_item.save()

            count = 0
            total = 0
            if request.data.get('complete') is not None:
                for entry in checklist_items.objects.filter(checklist=current_checklist_item.checklist):
                    if entry.complete is True:
                        count = count + 1
                    total = total + 1
                per = (count * 100) // total
                current_checklist_item.checklist.complete = str(per)
                current_checklist_item.checklist.save()

            new_activity = task_activity.objects.create(task=current_checklist_item.checklist.task, user=request.user,
                                                        action='updated checklist item',
                                                        target=current_checklist_item.item)
            new_activity.save()

            return JsonResponse({"Checklist_Item": "Updated"}, status=status.HTTP_200_OK)
        else:
            return JsonResponse({"Message": "Error you are not a member of this case"},
                                status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, checklist_item_id):
        current_checklist_item = checklist_items.objects.get(pk=checklist_item_id)
        if case_user_flag(current_checklist_item.checklist.task.task_case,
                          request.user) and current_checklist_item.checklist.task.completed is None:

            current_checklist = current_checklist_item.checklist
            current_checklist_item.delete()

            count = 0
            total = 0
            for entry in checklist_items.objects.filter(checklist=current_checklist):
                if entry.complete is True:
                    count = count + 1
                total = total + 1
            per = (count * 100) // total
            current_checklist_item.checklist.complete = str(per)
            current_checklist_item.checklist.save()

            return JsonResponse({"Checklist_Item": "Deleted"}, status=status.HTTP_200_OK)
        else:
            return JsonResponse({"Message": "Error you are not a member of this case"},
                                status=status.HTTP_400_BAD_REQUEST)


class add_task_label(APIView):
    permission_classes = ([IsAuthenticated])

    def get(self, request, task_id):
        current_task = task.objects.get(pk=task_id)
        if case_user_flag(current_task.task_case, request.user) or case_client_flag(current_task.task_case,
                                                                                    request.user):
            label_set = task_labels.objects.filter(task=current_task)
            serializer = task_label_serializer(label_set, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)
        else:
            return JsonResponse({"Message": "Error you are not a member of this case"},
                                status=status.HTTP_400_BAD_REQUEST)

    def post(self, request, task_id):
        current_task = task.objects.get(pk=task_id)
        if case_user_flag(current_task.task_case, request.user) and current_task.completed is None:
            new_label = task_labels.objects.create(task=current_task, label=request.data['label'])
            new_label.save()

            new_activity = task_activity.objects.create(task=current_task, user=request.user,
                                                        action='added label', target=request.data['label'])
            new_activity.save()

            return JsonResponse({"label": "added"}, status=status.HTTP_200_OK)
        else:
            return JsonResponse({"Message": "Error you are not a member of this case"},
                                status=status.HTTP_400_BAD_REQUEST)


class delete_task_labels(APIView):
    permission_classes = ([IsAuthenticated])

    def delete(self, request, label_id):
        current_label = task_labels.objects.get(pk=label_id)
        if case_user_flag(current_label.task.task_case, request.user) and current_label.task.completed is None:
            current_label.delete()
            return JsonResponse({"label": "deleted"}, status=status.HTTP_200_OK)
        else:
            return JsonResponse({"Message": "Error you are not a member of this case"},
                                status=status.HTTP_400_BAD_REQUEST)


class show_case_activity(APIView):
    permission_classes = ([IsAuthenticated])

    def get(self, request, case_id):
        result = []
        current_case = case.objects.get(pk=case_id)
        if case_user_flag(current_case, request.user) or case_client_flag(current_case,
                                                                          request.user):
            task_set = current_case.task_set.all()
            for task_element in task_set:
                activity_set = task_activity.objects.filter(task=task_element).order_by('-updated_at')
                for element in activity_set:
                    dict1 = {'id': element.id,
                             'task': {'id': element.task.id, 'name': element.task.task_name},
                             'action': element.action,
                             'target': element.target,
                             'user': {'id': element.user.id,
                                      'username': element.user.username,
                                      'email': element.user.email,
                                      'profile': None,
                                      'image': None},
                             'created_at': element.created_at,
                             'updated_at': element.updated_at
                             }

                    profile_set = profile.objects.filter(user=element.user)
                    if len(profile_set) != 0:
                        dict1['user']['profile'] = profile_set[0].private
                        serializer = profile_image_serializer(profile_set[0])
                        dict1['user']['image'] = serializer.data
                    result.append(dict1)

            return JsonResponse(result, safe=False, status=status.HTTP_200_OK)
        else:
            return JsonResponse({"Message": "Error you are not a member of the case"},
                                status=status.HTTP_400_BAD_REQUEST)


class task_timer(APIView):
    permission_classes = [IsAuthenticated]

    def time_diff(self, value):
        value = value.total_seconds() // 1
        hours = value // 3600
        minutes = (value % 3600) // 60
        seconds = (value % 3600) % 60
        time_field = time(int(hours), int(minutes), int(seconds))
        return time_field

    def get(self, request, task_id, action):
        flag = 0
        current_task = task.objects.get(pk=task_id)
        if action == 'show':
            timer_set = timer.objects.filter(task=current_task)
            serializer = timer_serializer(timer_set, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)
        if case_user_flag(current_task.task_case, request.user) and current_task.completed is None:
            if action == 'start':
                current_timer = timer.objects.filter(task=current_task)
                for timers in current_timer:
                    if timers.status == 'end' or timers.end_time is None:
                        flag = 1
                if flag == 0:
                    start = timer.objects.create(task=current_task, start_time=datetime.now())
                    start.save()
                    return JsonResponse({"start": datetime.now()}, status=status.HTTP_200_OK)
                else:
                    return JsonResponse({"Message": "Error Timer already started or Timer endpoint has reached"},
                                        status=status.HTTP_400_BAD_REQUEST)
            elif action == 'pause':
                current_timer = timer.objects.filter(task=current_task)
                if len(current_timer) != 0:
                    obj = current_timer[len(current_timer) - 1]
                    if obj.end_time is None and obj.start_time is not None:
                        obj.end_time = datetime.now()
                        obj.start_time = obj.start_time.replace(tzinfo=pytz.UTC)
                        obj.end_time = obj.end_time.replace(tzinfo=pytz.UTC)
                        value = obj.end_time - obj.start_time
                        time_diff_obj = task_timer()
                        obj.time_spent = time_diff_obj.time_diff(value)
                        obj.status = 'pause'
                        obj.save()
                        return JsonResponse({"paused": obj.end_time}, status=status.HTTP_200_OK)
                return JsonResponse({"Message": " Error no timer is started"}, status=status.HTTP_400_BAD_REQUEST)
            elif action == 'end':
                current_timer = timer.objects.filter(task=current_task)
                if len(current_timer) != 0:
                    obj = current_timer[len(current_timer) - 1]
                    if obj.end_time is None and obj.start_time is not None:
                        obj.end_time = datetime.now()
                        obj.start_time = obj.start_time.replace(tzinfo=pytz.UTC)
                        obj.end_time = obj.end_time.replace(tzinfo=pytz.UTC)
                        value = obj.end_time - obj.start_time
                        time_diff_obj = task_timer()
                        obj.time_spent = time_diff_obj.time_diff(value)
                        obj.status = 'end'
                        obj.save()
                        return JsonResponse({"ended": obj.end_time})
                    elif obj.end_time is not None and obj.start_time is not None:
                        obj.status = 'end'
                        obj.save()
                        return JsonResponse({"timer": "ended"})
                return JsonResponse({'Message': 'Error no timer has started'})
        else:
            return JsonResponse({"ERROR": "You are not a member of the task"}, status=status.HTTP_400_BAD_REQUEST)


class Image(APIView):
    permission_classes = [IsAuthenticated]
    parser_classes = (MultiPartParser, FormParser)

    def get(self, request, task_id):
        try:
            current_task = task.objects.get(pk=task_id)
            if case_user_flag(current_task.task_case, request.user) or case_client_flag(current_task.task_case,
                                                                                        request.user):
                image_set = image.objects.filter(task=current_task).order_by('-created_at')
                serializer = task_images(image_set, many=True)
                result = []
                final = serializer.data
                for item, img in zip(final, image_set):
                    user = img.created_by
                    item['created_at'] = img.created_at
                    user_profile = profile.objects.filter(user=user)
                    image_serializer = profile_image_serializer(user_profile, many=True)

                    if len(user_profile) == 0:
                        dict1 = {'id': img.created_by.id, 'username': img.created_by.username,
                                 'image': None, 'private': None}
                        item['user'] = dict1
                    else:
                        item['user'] = {'id': img.created_by.id,
                                        'username': img.created_by.username,
                                        'email': img.created_by.email,
                                        'image': image_serializer.data[0],
                                        'private': user_profile[0].private}
                    result.append(item)

                return JsonResponse(result, safe=False, status=status.HTTP_200_OK)
            return JsonResponse({"ERROR": "Unauthorized access"}, status=status.HTTP_400_BAD_REQUEST)
        except:
            return JsonResponse([], safe=False, status=status.HTTP_200_OK)

    def post(self, request, task_id):
        current_task = task.objects.get(pk=task_id)
        if case_user_flag(current_task.task_case, request.user) and current_task.completed is None:
            serializer = task_images(data=request.data)
            if serializer.is_valid():
                serializer.validated_data['created_by'] = request.user
                serializer.validated_data['task'] = current_task
                serializer.save()
                return Response(serializer.data, status=status.HTTP_200_OK)
            if serializer.errors is not None:
                return Response({'Message': 'Error Filename must less than 500'})
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        else:
            return JsonResponse({"ERROR": "You are not a member of the case"}, status=status.HTTP_400_BAD_REQUEST)


class delete_Image(APIView):

    def get(self, request, img_id):
        try:
            img_entry = image.objects.get(pk=img_id)
            if case_user_flag(img_entry.task.task_case, request.user) or case_client_flag(img_entry.task.task_case,
                                                                                          request.user):
                serializer = task_images(img_entry)
                user_profile = profile.objects.filter(user=img_entry.created_by)
                image_serializer = profile_image_serializer(user_profile, many=True)
                final = serializer.data
                final['created_at'] = user_profile[0].created_at
                if len(user_profile) == 0:
                    final['user'] = {'id': img_entry.created_by.id,
                                     'username': img_entry.created_by.username,
                                     'email': img_entry.created_by.email,
                                     'image': None,
                                     'private': None
                                     }
                else:
                    final['user'] = {'id': img_entry.created_by.id,
                                     'username': img_entry.created_by.username,
                                     'email': img_entry.created_by.email,
                                     'image': image_serializer.data[0],
                                     'private': user_profile[0].private
                                     }
                return Response(final, status=status.HTTP_200_OK)
            return JsonResponse({"ERROR": "Unauthorized access"}, status=status.HTTP_400_BAD_REQUEST)
        except:
            return JsonResponse({"ERROR": "Image does not exist"}, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, img_id):
        try:
            img_entry = image.objects.get(pk=img_id)
            if (case_user_flag(img_entry.task.task_case, request.user) or case_client_flag(img_entry.task.task_case,
                                                                                           request.user)) and img_entry.task.completed is None:
                img_entry.delete()
                return JsonResponse({"Image": "Deleted"})
            return JsonResponse({"ERROR": "Unauthorized access"}, status=status.HTTP_400_BAD_REQUEST)
        except:
            return JsonResponse({"ERROR": "Image does not exist"}, status=status.HTTP_400_BAD_REQUEST)


class Document(APIView):
    permission_classes = [IsAuthenticated]
    parser_classes = (MultiPartParser, FormParser)

    def get(self, request, task_id):
        try:
            current_task = task.objects.get(pk=task_id)
            if case_user_flag(current_task.task_case, request.user) or case_client_flag(current_task.task_case,
                                                                                        request.user):
                doc_set = document.objects.filter(task=current_task).order_by('-created_at')
                serializer = task_documents(doc_set, many=True)
                result = []
                final = serializer.data
                for item, doc in zip(final, doc_set):
                    user = doc.created_by
                    item['created_at'] = doc.created_at
                    user_profile = profile.objects.filter(user=user)
                    image_serializer = profile_image_serializer(user_profile, many=True)
                    if len(user_profile) == 0:
                        dict1 = {'id': doc.created_by.id,
                                 'username': doc.created_by.username,
                                 'email': doc.created_by.email,
                                 'image': None,
                                 'private': None
                                 }
                        item['user'] = dict1
                    else:
                        item['user'] = {'id': doc.created_by.id,
                                        'username': doc.created_by.username,
                                        'email': doc.created_by.email,
                                        'image': image_serializer.data[0],
                                        'private': user_profile[0].private}
                    result.append(item)

                return JsonResponse(result, safe=False, status=status.HTTP_200_OK)
            return JsonResponse({"ERROR": "Unauthorized access"}, status=status.HTTP_400_BAD_REQUEST)
        except:
            return JsonResponse([], safe=False, status=status.HTTP_200_OK)

    def post(self, request, task_id):
        current_task = task.objects.get(pk=task_id)
        if case_user_flag(current_task.task_case, request.user) and current_task.completed is None:
            serializer = task_documents(data=request.data)
            if serializer.is_valid():
                serializer.validated_data['created_by'] = request.user
                serializer.validated_data['task'] = current_task
                serializer.save()
                return Response(serializer.data, status=status.HTTP_200_OK)
            if serializer.errors is not None:
                return Response({'Message': 'Error Filename must less than 500'})
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        else:
            return JsonResponse({"ERROR": "You are not a member of the task"}, status=status.HTTP_400_BAD_REQUEST)


class delete_Document(APIView):

    def get(self, request, doc_id):
        try:
            doc_entry = document.objects.get(pk=doc_id)
            if case_user_flag(doc_entry.task.task_case, request.user) or case_client_flag(doc_entry.task.task_case,
                                                                                          request.user):
                serializer = task_documents(doc_entry)
                user_profile = profile.objects.filter(user=doc_entry.created_by)
                image_serializer = profile_image_serializer(user_profile, many=True)
                final = serializer.data
                final['created_at'] = user_profile[0].created_at
                if len(user_profile) == 0:
                    final['user'] = {'id': doc_entry.created_by.id,
                                     'username': doc_entry.created_by.username,
                                     'email': doc_entry.created_by.email,
                                     'image': []
                                     }
                else:
                    final['user'] = {'id': doc_entry.created_by.id,
                                     'username': doc_entry.created_by.username,
                                     'email': doc_entry.created_by.email,
                                     'image': image_serializer.data[0],
                                     'private': user_profile[0].private
                                     }
                return Response(final, status=status.HTTP_200_OK)
            return JsonResponse({"ERROR": "Unauthorized access"}, status=status.HTTP_400_BAD_REQUEST)
        except:
            return JsonResponse({"ERROR": "Document does not exist"}, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, doc_id):
        try:
            doc_entry = document.objects.get(pk=doc_id)
            if (case_user_flag(doc_entry.task.task_case, request.user) or case_client_flag(doc_entry.task.task_case,
                                                                                           request.user)) and doc_entry.task.completed is None:
                doc_entry.delete()
                return JsonResponse({"doc": "Deleted"}, status=status.HTTP_200_OK)
            return JsonResponse({"ERROR": "Unauthorized access"}, status=status.HTTP_400_BAD_REQUEST)
        except:
            return JsonResponse({"ERROR": "Document does not exist"}, status=status.HTTP_400_BAD_REQUEST)


class task_completed(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, task_id):
        current_task = task.objects.get(pk=task_id)
        if request.user == current_task.created_by:
            if current_task.completed is None:
                timer_set = timer.objects.filter(task=current_task)
                if len(timer_set) != 0:
                    if timer_set[len(timer_set) - 1].status == 'end':
                        current_task.completed = datetime.now()
                        current_task.save()
                        return JsonResponse({'Task': 'Completed'}, status=status.HTTP_200_OK)
                    else:
                        return JsonResponse({'Message': 'Error Task cannot be completed while timer is active'},
                                            status=status.HTTP_400_BAD_REQUEST)
                else:
                    current_task.completed = datetime.now()
                    current_task.save()
                    return JsonResponse({'Task': 'Completed'}, status=status.HTTP_200_OK)
            else:
                return JsonResponse({'Message': 'Error Task is already completed'}, status=status.HTTP_400_BAD_REQUEST)
        return JsonResponse({'Message': 'Only task admin can mark a task to be completed'},
                            status=status.HTTP_400_BAD_REQUEST)


class case_completed(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, case_id):
        current_case = case.objects.get(pk=case_id)
        if request.user == current_case.created_by:
            task_set = task.objects.filter(task_case=current_case)
            for element in task_set:
                if element.completed is None:
                    timer_set = timer.objects.filter(task=element)
                    if len(timer_set) != 0:
                        if timer_set[len(timer_set) - 1].status == 'end':
                            element.completed = datetime.now()
                            element.save()
                        else:
                            return JsonResponse({'Message': {'Error Task cannot be completed while timer is active': {'task': {'id': element.id,
                                                                                                                               'name': element.task_name}}}},
                                                status=status.HTTP_400_BAD_REQUEST)
                    else:
                        element.completed = datetime.now()
                        element.save()
                else:
                    return JsonResponse({'Message': 'Error Task is already completed'},
                                        status=status.HTTP_400_BAD_REQUEST)
            current_case.completed = datetime.now()
            current_case.save()
            return JsonResponse({'Case': 'Completed'}, status=status.HTTP_200_OK)
        return JsonResponse({'Message': 'Only case admin can mark a case to be completed'},
                            status=status.HTTP_400_BAD_REQUEST)


class closed_cases(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        result = []
        case_set_member = request.user.case_members.exclude(completed__isnull=True)
        case_set_client = request.user.case_clients.exclude(completed__isnull=True)

        if len(case_set_member) != 0 or len(case_set_client) != 0:
            serializer = case_show_serializer(case_set_member, many=True)
            obj = case_show_serializer()
            final = obj.show(serializer.data)
            result = final
            serializer = case_show_serializer(case_set_client, many=True)
            final = obj.show(serializer.data)
            result = result + final
            return JsonResponse(result, safe=False, status=status.HTTP_200_OK)
        else:
            return JsonResponse([], safe=False, status=status.HTTP_200_OK)






