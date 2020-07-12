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
from .models import *
from datetime import datetime, timedelta
from chat.models import *
from chat.serializer import *
import json
import zipfile
from chat.views import *
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


class show_cases_as_member(APIView):
    permission_classes = ([IsAuthenticated])

    def get(self, request):
        user = User.objects.get(pk=request.user.id)
        case_set_member = user.case_members.all()

        if len(case_set_member) != 0:
            serializer = case_show_serializer(case_set_member, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)
        else:
            return JsonResponse({"ALERT": "You have no cases as member"})


class show_cases_as_client(APIView):
    permission_classes = ([IsAuthenticated])

    def get(self, request):
        user = User.objects.get(pk=request.user.id)
        case_set_client = user.case_clients.all()

        if len(case_set_client) != 0:
            serializer = case_show_serializer(case_set_client, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)
        else:
            return JsonResponse({"ALERT": "You have no cases as client"})


class show_case(APIView):
    permission_classes = ([IsAuthenticated])

    def get(self, request, case_id, format='json'):
        result = []
        list1 = []
        queryset = case.objects.filter(pk=case_id)
        serializer = case_show_serializer(queryset, many=True)
        current_case = case.objects.get(pk=case_id)
        task_set = current_case.task_set.all()
        for task_element in task_set:
            list1.append(task_element.id)
        result.append(serializer.data)
        result.append({"tasks": list1})
        return JsonResponse(result, safe=False)

    def put(self, request, case_id):
        current_case = case.objects.get(pk=case_id)
        if case_user_flag(current_case, request.user):
            current_case.case_name = request.data['case_name']
            obj = current_case.save()
            return JsonResponse({"Case": "Updated"})

    def delete(self, request, case_id, format=None):
        current_case = case.objects.get(pk=case_id)
        if request.user.id == current_case.created_by.id:
            current_case.delete()
            return JsonResponse({"Case": "Deleted"})


class case_assign_members(APIView):
    permission_classes = ([IsAuthenticated])

    def post(self, request, case_id, format='json'):
        current_case = case.objects.get(pk=case_id)

        if case_user_flag(current_case, request.user):
            already_member = []
            already_client = []

            for member_id in request.data['case_members']:
                user = User.objects.get(pk=member_id)
                existing_member = current_case.case_members.filter(pk=user.id)
                existing_client = current_case.case_clients.filter(pk=user.id)

                if len(existing_member) != 0:
                    already_member.append(member_id)
                elif len(existing_client) != 0:
                    already_client.append(member_id)
                else:
                    invite_user = invite.objects.create(case=current_case, sent_to=user, position='case_member', sent_from=request.user)
                    invite_user.save()

            if len(already_member) == 0 and len(already_client) == 0:
                return JsonResponse({"Invite": "Sent"})
            elif len(already_member) != 0 or len(already_client) != 0:
                return JsonResponse(
                    {"ALERT users are already members": already_member, "users are already clients": already_client,
                     "rest of the members are": "added"})
        else:
            return JsonResponse({"ERROR": "You are not authorized to add members to this case"})

    def delete(self, request, case_id):
        current_case = case.objects.get(pk=case_id)
        current_chat = chat.objects.get(case=current_case)

        if case_user_flag(current_case, request.user):
            for member in request.data['case_members']:
                user = User.objects.get(pk=member)
                existing_member = current_case.case_members.filter(pk=user.id)
                if len(existing_member) == 0:
                    return JsonResponse({"ERROR": "User is not a member of this case"})
                current_case.case_members.remove(user)
                current_chat.chat_members.remove(user)

            return JsonResponse({"Case": "Members removed"})
        else:
            return JsonResponse({"ERROR": "You are not authorized to remove members from this case"})


class case_assign_clients(APIView):
    permission_classes = ([IsAuthenticated])

    def post(self, request, case_id, format='json'):
        current_case = case.objects.get(pk=case_id)

        if case_user_flag(current_case, request.user):
            already_member = []
            already_client = []

            for client_id in request.data['case_clients']:
                user = User.objects.get(pk=client_id)
                existing_member = current_case.case_members.filter(pk=user.id)
                existing_client = current_case.case_clients.filter(pk=user.id)

                if len(existing_member) != 0:
                    already_member.append(client_id)
                elif len(existing_client) != 0:
                    already_client.append(client_id)
                else:
                    invite_user = invite.objects.create(case=current_case, sent_to=user, position='case_client', sent_from=request.user)
                    invite_user.save()

            if len(already_member) == 0 and len(already_client) == 0:
                return JsonResponse({"Invite": "Sent"})
            elif len(already_member) != 0 or len(already_client) != 0:
                return JsonResponse(
                    {"ALERT users are already members": already_member, "users are already clients": already_client,
                     "rest of the clients are": "added"})
        else:
            return JsonResponse({"ERROR": "You are not authorized to add clients to this case"})

    def delete(self, request, case_id):
        current_case = case.objects.get(pk=case_id)
        current_chat = chat.objects.get(case=current_case)

        if case_user_flag(current_case, request.user):
            for member in request.data['case_clients']:
                user = User.objects.get(pk=member)
                current_case.case_clients.remove(user)
                current_chat.chat_members.remove(user)

            return JsonResponse({"clients": "Removed"})
        else:
            return JsonResponse({"ERROR": "You are not authorized to remove members from this case"})


class add_task(APIView):
    permission_classes = ([IsAuthenticated])

    def post(self, request, case_id, foramt='json'):
        current_case = case.objects.get(pk=case_id)
        result = []
        if case_user_flag(current_case, request.user):
            serializer = task_create_serializer(data=request.data)
            if serializer.is_valid():
                serializer.validated_data['task_case'] = current_case  # create task
                serializer.validated_data['created_by'] = request.user
                serializer.validated_data['task_members'] = [request.user]
                serializer.save()

                new_task_set = task.objects.all()
                new_task = new_task_set[len(new_task_set) - 1]
                new_activity = task_activity.objects.create(task=new_task, user=request.user,
                                                            action="created task")  # activity
                new_activity.save()

                return Response(serializer.data, status=status.HTTP_201_CREATED)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        else:
            return JsonResponse({"Error": "you are not a case member"})


class add_task_members(APIView):
    permission_classes = ([IsAuthenticated])

    def post(self, request, task_id):
        current_task = task.objects.get(pk=task_id)
        prob = []
        if task_user_flag(current_task, request.user):
            member_set = request.data['task_members']
            for member in member_set:
                user = User.objects.get(pk=member)
                for case_member in current_task.task_case.case_members.all():
                    if case_member.id == member:
                        current_task.task_members.add(user)

                        new_activity = task_activity.objects.create(task=current_task, user=request.user,
                                                                    action="updated task members")  # activity
                        new_activity.save()
                        break
                    else:
                        prob.append(member)
                        break
            if len(prob) == 0:
                return JsonResponse({"Task_Members": "Added"})
            else:
                return JsonResponse(
                    {"ERROR Given users are not assigned as case members and cannot be added as task members": prob})
        else:
            return JsonResponse({"ERROR": "You are not authorized to add member to this task"})

    def delete(self, request, task_id):
        current_task = task.objects.get(pk=task_id)
        if case_user_flag(current_task.task_case, request.user):
            for member_id in request.data['task_members']:
                user = User.objects.get(pk=member_id)
                current_task.task_members.remove(user)
                return JsonResponse({"task_members": "Deleted"})
        else:
            return JsonResponse({"ERROR": "You are not a member of this case"})


class show_task_complete(APIView):
    permission_classes = ([IsAuthenticated])

    def get(self, request, task_id):
        current_task = task.objects.get(pk=task_id)
        result = []
        if case_user_flag(current_task.task_case, request.user) or case_client_flag(current_task.task_case,
                                                                                    request.user):
            serializer = task_show_serializer(current_task)
            result.append(serializer.data)

            comments_set = comments.objects.filter(task=current_task)
            if len(comments_set) != 0:
                serializer1 = task_comments_serializer(comments_set, many=True)
                result.append({"comments": serializer1.data})
            else:
                result.append({"comments": "None"})

            checklist_set = checklist.objects.filter(task=current_task)
            if len(checklist_set) != 0:
                serializer2 = task_checklist_serializer(checklist_set, many=True)
                result.append({"checklist": serializer2.data})

                for element in checklist_set:
                    checklist_items_set = checklist_items.objects.filter(checklist=element)

                    if len(checklist_items_set) != 0:
                        serializer3 = checklist_items_serializer(checklist_items_set, many=True)
                        result.append({"checklist_items": serializer3.data})
                    else:
                        result.append({"no_checklist_items": element.id})
            else:
                result.append({"checklist": "None"})

            label_set = task_labels.objects.filter(task=current_task)
            if len(label_set) != 0:
                serializer4 = task_label_serializer(label_set, many=True)
                result.append({"labels": serializer4.data})
            else:
                result.append({"Labels": "None"})

            return JsonResponse(result, safe=False)
        else:
            return JsonResponse({"ERROR": "You are not a member of this case"})

    def put(self, request, task_id):
        current_task = task.objects.get(pk=task_id)
        if case_user_flag(current_task.task_case, request.user):
            current_task.task_name = request.data["task_name"]
            current_task.save()

            new_activity = task_activity.objects.create(task=current_task, user=request.user,
                                                        action='updated task_name')
            new_activity.save()

            return JsonResponse({"task": "Updated"})
        else:
            return JsonResponse({"ERROR": "You are not a member of this case"})

    def delete(self, request, task_id):
        current_task = task.objects.get(pk=task_id)
        if case_user_flag(current_task.task_case, request.user):

            new_activity = task_activity.objects.create(task=current_task, user=request.user, action='deleted')
            new_activity.save()

            current_task.delete()
            return JsonResponse({"task": "deleted"})
        else:
            return JsonResponse({"ERROR": "You are not a member of this case"})


class add_task_details(APIView):
    permission_classes = ([IsAuthenticated])

    def get(self, request, task_id):
        current_task = task.objects.get(pk=task_id)
        if case_user_flag(current_task.task_case, request.user) or case_client_flag(current_task.task_case,
                                                                                    request.user):
            json = {"details": current_task.details}
            return JsonResponse(json)
        else:
            return JsonResponse({"ERROR": "You are not a member or client of this case"})

    def post(self, request, task_id):
        current_task = task.objects.get(pk=task_id)
        if case_user_flag(current_task.task_case, request.user):
            current_task.details = request.data['details']
            current_task.save()

            new_activity = task_activity.objects.create(task=current_task, user=request.user, action='added details')
            new_activity.save()

            return JsonResponse({"detail": "added"})
        else:
            return JsonResponse({"ERROR": "You are not a member of this case"})


class add_task_comment(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, task_id):
        current_task = task.objects.get(pk=task_id)
        if case_user_flag(current_task.task_case, request.user) or case_client_flag(current_task.task_case,
                                                                                    request.user):
            task_comments = comments.objects.filter(task=current_task)
            serializer = task_comments_serializer(task_comments, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)
        else:
            return JsonResponse({"ERROR": "You are not a member of this case"})

    def post(self, request, task_id):
        current_task = task.objects.get(pk=task_id)
        if case_user_flag(current_task.task_case, request.user) or case_client_flag(current_task.task_case,
                                                                                    request.user):
            new_comment = comments.objects.create(task=current_task, comment=request.data['comment'],
                                                  comment_user=request.user)
            new_comment.save()

            new_activity = task_activity.objects.create(task=current_task, user=request.user, action='added comment')
            new_activity.save()

            return JsonResponse({"comment": "added"})
        else:
            return JsonResponse({"ERROR": "You are not a member of this case"})


class edit_task_comment(APIView):
    permission_classes = ([IsAuthenticated])

    def put(self, request, comment_id):
        current_comment = comments.objects.get(pk=comment_id)
        if request.user.id == current_comment.comment_user.id:
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
        if request.user.id == current_comment.comment_user.id:
            current_comment.delete()
            return JsonResponse({"comment": "deleted"})
        else:
            return JsonResponse({"ERROR": "You did not create this comment"})


class add_task_checklist(APIView):
    permission_classes = ([IsAuthenticated])

    def get(self, request, task_id):
        current_task = task.objects.get(pk=task_id)
        if case_user_flag(current_task.task_case, request.user) or case_client_flag(current_task.task_case,
                                                                                    request.user):
            checklist_set = checklist.objects.filter(task=current_task)
            serializer = task_checklist_serializer(checklist_set, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)
        else:
            return JsonResponse({"ERROR": "You are not a member of this case"})

    def post(self, request, task_id):
        current_task = task.objects.get(pk=task_id)
        if case_user_flag(current_task.task_case, request.user):
            new_checklist = checklist.objects.create(task=current_task, checklist_name=request.data['checklist_name'],
                                                     created_by=request.user)
            new_checklist.save()

            new_activity = task_activity.objects.create(task=current_task, user=request.user, action='added checklist')
            new_activity.save()

            return JsonResponse({"Checklist": "Created"})
        else:
            return JsonResponse({"ERROR": "You are not member of this case"})


class edit_task_checklist(APIView):
    permission_classes = ([IsAuthenticated])

    def put(self, request, checklist_id):
        current_checklist = checklist.objects.get(pk=checklist_id)
        if case_user_flag(current_checklist.task.task_case, request.user):
            current_checklist.checklist_name = request.data['checklist_name']
            current_checklist.save()

            new_activity = task_activity.objects.create(task=current_checklist.task, user=request.user,
                                                        action='updated checklist')
            new_activity.save()

            return JsonResponse({"Checklist": "Updated"})
        else:
            return JsonResponse({"ERROR": "You are not a member of this case"})

    def delete(self, request, checklist_id):
        current_checklist = checklist.objects.get(pk=checklist_id)
        if case_user_flag(current_checklist.task.task_case, request.user):
            current_checklist.delete()
            return JsonResponse({"Checklist": "Deleted"})
        else:
            return JsonResponse({"ERROR": "You are not a member of this case"})


class add_task_checklist_items(APIView):
    permission_classes = ([IsAuthenticated])

    def post(self, request, checklist_id):
        current_checklist = checklist.objects.get(pk=checklist_id)
        if case_user_flag(current_checklist.task.task_case, request.user):
            new_item = checklist_items.objects.create(checklist=current_checklist, item=request.data['item'])
            new_item.save()

            new_activity = task_activity.objects.create(task=current_checklist.task, user=request.user,
                                                        action='added item to checklist')
            new_activity.save()

            return JsonResponse({"Checklist": "Item_added"})
        else:
            return JsonResponse({"ERROR": "You are not a member of this case"})


class edit_checklist_items(APIView):
    permission_classes = ([IsAuthenticated])

    def put(self, request, checklist_item_id):
        current_checklist_item = checklist_items.objects.get(pk=checklist_item_id)
        if case_user_flag(current_checklist_item.checklist.task.task_case, request.user):
            current_checklist_item.item = request.data['item']
            current_checklist_item.save()

            new_activity = task_activity.objects.create(task=current_checklist_item.checklist.task, user=request.user,
                                                        action='Updated item in checklist')
            new_activity.save()

            return JsonResponse({"Checklist_Item": "Updated"})
        else:
            return JsonResponse({"ERROR": "You are not a member of this case"})

    def delete(self, request, checklist_item_id):
        current_checklist_item = checklist_items.objects.get(pk=checklist_item_id)
        if case_user_flag(current_checklist_item.checklist.task.task_case, request.user):
            current_checklist_item.delete()
            return JsonResponse({"Checklist_Item": "Deleted"})
        else:
            return JsonResponse({"ERROR": "You are not a member of this case"})


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
            return JsonResponse({"ERROR": "You are not a member of this case"})

    def post(self, request, task_id):
        current_task = task.objects.get(pk=task_id)
        if case_user_flag(current_task.task_case, request.user):
            new_label = task_labels.objects.create(task=current_task, label=request.data['label'])
            new_label.save()

            new_activity = task_activity.objects.create(task=current_task, user=request.user, action='added label')
            new_activity.save()

            return JsonResponse({"label": "added"})
        else:
            return JsonResponse({"ERROR": "You are not a member of this case"})


class delete_task_labels(APIView):
    permission_classes = ([IsAuthenticated])

    def delete(self, request, label_id):
        current_label = task_labels.objects.get(pk=label_id)
        if case_user_flag(current_label.task.task_case, request.user):
            current_label.delete()
            return JsonResponse({"label": "deleted"})
        else:
            return JsonResponse({"ERROR": "You are not a member of this case"})


class add_due_date(APIView):
    permission_classes = ([IsAuthenticated])

    def post(self, request, task_id):
        current_task = task.objects.get(pk=task_id)
        if case_user_flag(current_task.task_case, request.user):
            datetime_object = datetime.strptime(request.data['due_date'], '%y/%m/%d %H:%M:%S')
            current_task.due_date = datetime_object
            current_task.save()

            new_activity = task_activity.objects.create(task=current_task, user=request.user, action='added due date')
            new_activity.save()

            return JsonResponse({"due_date": "Added"})
        else:
            return JsonResponse({"ERROR": "You are not a member of this case"})


class show_case_activity(APIView):
    permission_classes = ([IsAuthenticated])

    def get(self, request, case_id):
        result = []
        current_case = case.objects.get(pk=case_id)
        if case_user_flag(current_case, request.user) or case_client_flag(current_case,
                                                                          request.user):
            task_set = current_case.task_set.all()
            for task in task_set:
                activity_set = task_activity.objects.filter(task=task)
                serializer = activity_serializer(activity_set, many=True)
                result.append(serializer.data)
            return JsonResponse(result, safe=False)
        else:
            return JsonResponse({"ERROR": "You are not a member of the case"})


class task_timer(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, task_id, action):
        flag = 0
        current_task = task.objects.get(pk=task_id)
        if case_user_flag(current_task.task_case, request.user):
            if action == 'start':
                current_timer = timer.objects.filter(task=current_task)
                for timers in current_timer:
                    if timers.status == 'end' or timers.end_time is None:
                        flag = 1
                if flag == 0:
                    start = timer.objects.create(task=current_task, start_time=datetime.now())
                    start.save()
                    return JsonResponse({"start": datetime.now()})
                else:
                    return JsonResponse({"error": "Timer already started or Timer endpoint has reached"})
            elif action == 'pause':
                current_timer = timer.objects.filter(task=current_task)
                obj = current_timer[len(current_timer) - 1]
                if obj.end_time is None and obj.start_time is not None:
                    obj.end_time = datetime.now()
                    obj.status = 'pause'
                    obj.save()
                    return JsonResponse({"timer": "paused"})
                else:
                    return JsonResponse({"error": "no timer is started"})
            elif action == 'end':
                current_timer = timer.objects.filter(task=current_task)
                obj = current_timer[len(current_timer) - 1]
                if obj.end_time is None and obj.start_time is not None:
                    obj.end_time = datetime.now()
                    obj.status = 'end'
                    obj.save()
                    return JsonResponse({"timer": "ended"})
                elif obj.end_time is not None and obj.start_time is not None:
                    obj.status = 'end'
                    obj.save()
                    return JsonResponse({"timer": "ended"})
            elif action == 'show':
                timer_set = timer.objects.filter(task=current_task)
                serializer = timer_serializer(timer_set, many=True)
                return Response(serializer.data, status=status.HTTP_200_OK)
        else:
            return JsonResponse({"ERROR": "You are not a member of the task"})


class Image(APIView):
    permission_classes = [IsAuthenticated]
    parser_classes = (MultiPartParser, FormParser)

    def get(self, request, task_id):
        current_task = task.objects.get(pk=task_id)
        if case_user_flag(current_task.task_case, request.user) or case_client_flag(current_task.task_case, request.user):
            image_set = image.objects.filter(task=current_task)
            serializer = task_images(image_set, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)
        return JsonResponse({"ERROR": "Unauthorized access"})

    def post(self, request, task_id):
        current_task = task.objects.get(pk=task_id)
        if case_user_flag(current_task.task_case, request.user):
            serializer = task_images(data=request.data)
            if serializer.is_valid():
                serializer.validated_data['created_by'] = request.user
                serializer.validated_data['task'] = current_task
                serializer.save()
                return Response(serializer.data, status=status.HTTP_200_OK)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        else:
            return JsonResponse({"ERROR": "You are not a member of the case"})


class delete_Image(APIView):

    def get(self, request, img_id):
        try:
            img_entry = image.objects.get(pk=img_id)
            if case_user_flag(img_entry.task.task_case, request.user) or case_client_flag(img_entry.task.task_case,
                                                                                          request.user):
                serializer = task_images(img_entry)
                return Response(serializer.data, status=status.HTTP_200_OK)
            return JsonResponse({"ERROR": "Unauthorized access"})
        except:
            return JsonResponse({"ERROR": "Image does not exist"})

    def delete(self, request, img_id):
        try:
            img_entry = image.objects.get(pk=img_id)
            if case_user_flag(img_entry.task.task_case, request.user) or case_client_flag(img_entry.task.task_case,
                                                                                        request.user):
                img_entry.delete()
                return JsonResponse({"Image": "Deleted"})
            return JsonResponse({"ERROR": "Unauthorized access"})
        except:
            return JsonResponse({"ERROR": "Image does not exist"})


class Document(APIView):
    permission_classes = [IsAuthenticated]
    parser_classes = (MultiPartParser, FormParser)

    def get(self, request, task_id):
        current_task = task.objects.get(pk=task_id)
        if case_user_flag(current_task.task_case, request.user) or case_client_flag(current_task.task_case,
                                                                                    request.user):
            doc_set = document.objects.filter(task=current_task)
            serializer = task_images(doc_set, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)
        return JsonResponse({"ERROR": "Unauthorized access"})

    def post(self, request, task_id):
        current_task = task.objects.get(pk=task_id)
        if case_user_flag(current_task.task_case, request.user):
            serializer = task_documents(data=request.data)
            if serializer.is_valid():
                serializer.validated_data['created_by'] = request.user
                serializer.validated_data['task'] = current_task
                serializer.save()
                return Response(serializer.data, status=status.HTTP_200_OK)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        else:
            return JsonResponse({"ERROR": "You are not a member of the task"})


class task_billing_type(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, task_id):
        current_task = task.objects.get(pk=task_id)
        if case_user_flag(current_task.task_case, request.user):
            current_task.billing_type = request.data['billing_type']
            current_task.save()
            return JsonResponse({"billing_type": "Added"})


class add_task_cost(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, task_id):
        current_task = task.objects.get(pk=task_id)
        if case_user_flag(current_task.task_case, request.user):
            if current_task.billing_type == 'billing':
                current_task.invoice_type = request.data['invoice_type']
                current_task.cost = request.data['cost']
                current_task.save()
                return JsonResponse({"Cost": "Added to task"})
            else:
                return JsonResponse({"Task": "Not of type billing"})
        else:
            return JsonResponse({"ERROR": "You are not a member of the task"})
