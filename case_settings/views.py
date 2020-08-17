from django.shortcuts import render
from django.http import HttpResponse
from django.http import JsonResponse
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.contrib.auth.models import User
from cases.models import *
from cases.serializers import *
from datetime import datetime, date, timedelta
from chat.models import *
from chat.serializer import *
import json
import zipfile
from chat.views import *
from user.serializers import *
from user.models import *
import os
from django.core.mail import send_mail, EmailMessage
from .tasks import *
from .models import *
from rest_framework import status
from rest_framework.authtoken.models import Token
from .serializers import *


# Create your views here.

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

def get_all_docs(case_id, zip1):
    current_case = case.objects.get(pk=case_id)
    try:
        folder_path = 'media/' + str(current_case.case_name) + 'doc' + '/documents/'
        var = os.listdir(folder_path)
        for user in var:
            folder_path = folder_path + user + '/'
            doc_set = os.listdir(folder_path)
            for doc in doc_set:
                zip1.write(folder_path + doc)
    except:
        pass


def get_all_img(case_id, zip1):
    current_case = case.objects.get(pk=case_id)
    try:
        folder_path = 'media/' + str(current_case.case_name) + 'img' + '/images/'
        var = os.listdir(folder_path)
        for user in var:
            folder_path = folder_path + user + '/'
            img_set = os.listdir(folder_path)
            for img in img_set:
                zip1.write(folder_path + img)
    except:
        pass


def get_case_chat_info(case_id, zip1):
    current_case = case.objects.get(pk=case_id)
    current_chat = chat.objects.get(case=current_case)
    f = open('chat/chat_files/case_chat.txt', 'w')
    message_set = current_chat.message_set.all()
    for message_obj in message_set:
        message_string = str(message_obj.created_at) + ' ' + str(message_obj.created_by) + ' ' + message_obj.content
        f.write(message_string + '\n')
    f.close()
    zip1.write('chat/chat_files/case_chat.txt')


def get_case_task_info(case_id, zip1):
    current_case = case.objects.get(pk=case_id)
    task_set = current_case.task_set.all()
    f = open('cases/case_files/case_task.txt', 'w')

    f.write('CASE ID:  ' + str(current_case.id) + '\n' + 'Case Name:  ' + str(
        current_case.case_name) + '\n' + 'Case Members:  ')
    for member in current_case.case_members.all():
        f.write(member.username + ', ')
    f.write('\n' + 'Case Clients:  ')
    if len(current_case.case_clients.all()) != 0:
        for client in current_case.case_clients.all():
            f.write(client.username + ', ')
    else:
        f.write('None')
    f.write('\n\n')

    if len(task_set) != 0:
        for task_obj in task_set:
            f.write(
                'ID: ' + str(task_obj.id) + '\n' + 'Task Name:  ' + str(
                    task_obj.task_name) + '\n' + '\n' + 'Details:  ' +
                str(task_obj.details) + '\n' + 'Task Member:  ')
            for member in task_obj.task_members.all():
                f.write(str(member.username) + ', ')
            f.write('\n' + 'Admin:  ' + task_obj.created_by.username + '\n' + 'Created At:  ' + str(
                task_obj.created_at) + '\n'
                    + 'Last Updated At:  ' + str(task_obj.updated_at) + '\n' + 'Billing Type:  ' + str(
                task_obj.billing_type) + '\n')

            comment_set = task_obj.comments_set.all()
            if len(comment_set) != 0:
                f.write('\n' + 'Comments :' + '\n')
                for comment_obj in comment_set:
                    f.write(str(
                        comment_obj.created_at) + ' ' + comment_obj.comment_user.username + '->' + comment_obj.comment + '\n')

            checklist_set = task_obj.checklist_set.all()
            if len(checklist_set) != 0:
                f.write('\n' + 'Checklists :' + '\n')
                for checklist_obj in checklist_set:
                    f.write('  ' + checklist_obj.checklist_name + ': ' + '\n')
                    checklist_items_set = checklist_obj.checklist_items_set.all()
                    if len(checklist_items_set) != 0:
                        for checklist_items_obj in checklist_items_set:
                            f.write('    ' + checklist_items_obj.item + '\n')

            label_set = task_obj.task_labels_set.all()
            if len(label_set) != 0:
                f.write('\n' + 'Labels:  ')
                for label_obj in label_set:
                    f.write(label_obj.label + ',  ')

            try:
                task_invoice_obj = task_invoice.objects.get(task=task_obj)
                f.write('\n\n' + 'Invoice:  ' + '\n')
                f.write('  ' + 'Invoice Type:  ' + task_obj.invoice_type + '\n' + '  ' + 'Cost:  ' + str(
                    task_obj.cost) + '\n' +
                        '  ' + 'Time On Task(In Hours):  ' + str(
                    float(task_invoice_obj.total_cost) / float(task_obj.cost)) + '\n' + '  '
                        + 'Total Cost:  ' + str(task_invoice_obj.total_cost))
            except:
                pass

            f.write('\n\n')
        f.close()
        zip1.write('cases/case_files/case_task.txt')
    else:
        f.write('No Tasks')
        f.close()
        zip1.write('cases/case_files/case_task.txt')


class get_all_case_info(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, case_id):
        zip1 = zipfile.ZipFile('zip/case.zip', 'w')
        get_case_chat_info(case_id, zip1)
        get_case_task_info(case_id, zip1)
        get_all_img(case_id, zip1)
        get_all_docs(case_id, zip1)

        email = EmailMessage(
            'Hello',
            'Case Details',
            'chiragsharma1061@gmail.com',
            ['chirag2214@outlook.com'],
        )
        zip1.close()

        email.attach_file('zip/case.zip')

        email.send()

        return JsonResponse({"Text_File": "Added"})


class index(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, case_id):
        send_case_email.delay(case_id)
        return JsonResponse({'done': 'done'})


def invoice_category(request, new_cost, current_task):
    if request.data.get('category') == 'single' or request.data.get('category') is None:
        if request.data.get('frequency') == 1 or request.data.get('frequency') is None:
            invoice = task_invoice.objects.create(task=current_task, total_cost=new_cost)
            x = invoice.save()

            payment = invoice_payment.objects.create(invoice=invoice, payment=new_cost)
            payment.save()
            return invoice.id
        return {"Message": "Error When Category is Single frequency must be equal to 1"}

    elif request.data.get('category') == 'equal':
        if 1 < request.data.get('frequency') <= 10:
            invoice = task_invoice.objects.create(task=current_task, total_cost=new_cost,
                                                  category=request.data.get('category'),
                                                  frequency=request.data.get('frequency'))
            x = invoice.save()

            loop = 0
            while loop < int(request.data.get('frequency')):
                cost = new_cost / int(request.data.get('frequency'))
                payment_obj = invoice_payment.objects.create(invoice=invoice, payment=cost)
                payment_obj.save()
                loop = loop + 1
            return invoice.id
        return {"Message": "Error when category is equal frequency must be greater than 1"}

    elif request.data.get('category') == 'random':
        total_payment = 0
        payment_count = 0
        for element in request.data.get('payment'):
            if element == 0:
                return {'Message': 'Payments must be non zero'}
            total_payment = total_payment + element
            payment_count = payment_count + 1
        if total_payment != new_cost:
            return {'Message': 'Sum of the payments must be equal to cost of the invoice'}
        if payment_count != int(request.data.get('frequency')):
            return {'Message': 'Payments must be equal to the frequency'}

        if 1 < request.data.get('frequency') <= 10:
            invoice = task_invoice.objects.create(task=current_task, total_cost=new_cost,
                                                  category=request.data.get('category'),
                                                  frequency=request.data.get('frequency'))
            x = invoice.save()

            loop = 0
            while loop < int(request.data.get('frequency')):
                payment_obj = invoice_payment.objects.create(invoice=invoice, payment=request.data['payment'][loop])
                payment_obj.save()
                loop = loop + 1
            return invoice.id
        return {"Message": "Error when category is random frequency must be greater than 1 and less than or equal to 10"}

    else:
        return {"Message": "Error Category must be one of the following SINGLE, EQUAL, RANDOM"}


def display_invoice(invoice_id):
    #       RESPONSE OF INVOICE

    invoice = task_invoice.objects.get(pk=invoice_id)
    dict1 = {
        'id': invoice.id, 'task': {
            'id': invoice.task.id, 'name': invoice.task.task_name,
            'billing_type': invoice.task.billing_type, 'invoice_type': invoice.task.invoice_type,
            'cost': invoice.task.cost,
            'case': {'id': invoice.task.task_case.id, 'name': invoice.task.task_case.case_name,
                     'admin': {'id': invoice.task.task_case.created_by.id,
                               'username': invoice.task.task_case.created_by.username,
                               'image': None,
                               'private': None}
                     }
        },
        'total_cost': invoice.total_cost, 'frequency': invoice.frequency, 'category': invoice.category,
        'created_at': invoice.created_at
    }

    user_profile = profile.objects.filter(user=invoice.task.task_case.created_by)
    if len(user_profile) != 0:
        serializer = profile_image_serializer(user_profile, many=True)
        dict1['task']['case']['admin']['image'] = serializer.data
        dict1['task']['case']['admin']['private'] = user_profile[0].private

    #       CASE CLIENTS IN INVOICE

    result = []
    for user in invoice.task.task_case.case_clients.all():
        dict2 = {'id': user.id, 'username': user.username, 'image': None, 'private': None}
        user_profile = profile.objects.filter(user=user)
        if len(user_profile) != 0:
            serializer = profile_image_serializer(user_profile, many=True)
            dict1['task']['case']['admin']['image'] = serializer.data
            dict1['task']['case']['admin']['private'] = user_profile[0].private
        result.append(dict2)
    dict1['task']['case']['clients'] = result

    #       PAYMENT SET IN INVOICE

    payment_obj = invoice_payment.objects.filter(invoice=invoice)
    serializer = invoice_payment_serializer(payment_obj, many=True)
    dict1['Payments'] = serializer.data

    return dict1


class task_invoice_view(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, task_id):
        current_task = task.objects.get(pk=task_id)
        if case_user_flag(current_task.task_case, request.user) or case_client_flag(current_task.task_case,
                                                                                    request.user):
            try:
                task_invoice_set = task_invoice.objects.get(task=current_task)
                dict1 = display_invoice(task_invoice_set.id)
                return JsonResponse(dict1, status=status.HTTP_200_OK)
            except:
                return JsonResponse({"Message": "Error No Invoice Exists"}, status=status.HTTP_400_BAD_REQUEST)
        else:
            return JsonResponse({"Message": "Error you are not a member of this case"}, status=status.HTTP_400_BAD_REQUEST)

    def post(self, request, task_id):
        current_task = task.objects.get(pk=task_id)

        try:
            current_invoice = task_invoice.objects.get(task=current_task)
            return JsonResponse({'Message': 'Error Invoice is already created for this task'},
                                status=status.HTTP_400_BAD_REQUEST)
        except:
            pass

        if request.user.id == current_task.task_case.created_by.id:

            if current_task.completed is not None:
                timer_set = timer.objects.filter(task=current_task)

                if current_task.invoice_type == 'hourly':
                    time_diff = 0
                    for interval in timer_set:
                        value = interval.start_time - interval.end_time                                     # calculating total cost for the invoice
                        time_diff = time_diff - float(value.seconds) / 3600 - float(value.days) * 24
                    total_cost = float(current_task.cost) * time_diff

                    response = invoice_category(request, total_cost, current_task)
                    if type(response) == int:
                        pass
                    else:
                        return JsonResponse(response, safe=False, status=status.HTTP_400_BAD_REQUEST)

                    dict1 = display_invoice(response)
                    return Response(dict1, status=status.HTTP_201_CREATED)

                elif current_task.invoice_type == 'onetime':

                    response = invoice_category(request, current_task.cost, current_task)
                    if type(response) == int:
                        pass
                    else:
                        return JsonResponse(response, safe=False, status=status.HTTP_400_BAD_REQUEST)

                    dict1 = display_invoice(response)
                    return Response(dict1, status=status.HTTP_201_CREATED)
                else:
                    return JsonResponse({"Message": "Error This task has billing_type as non billing therefore cannot generate invoice"}, status=status.HTTP_400_BAD_REQUEST)
            else:
                return JsonResponse({'Message': 'Error to create invoice task must be completed'}, status=status.HTTP_400_BAD_REQUEST)
        else:
            return JsonResponse({"Error": "you are not a member of this case"}, status=status.HTTP_400_BAD_REQUEST)


class invoice_payment_set(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, task_id):
        current_task = task.objects.get(pk=task_id)
        if case_user_flag(current_task.task_case, request.user) or case_client_flag(current_task.task_case,
                                                                                    request.user):
            try:
                current_invoice = task_invoice.objects.get(task=current_task)
                payment_entry_set = invoice_payment.objects.filter(invoice=current_invoice)
                serializer = invoice_payment_serializer(payment_entry_set, many=True)
                return Response(serializer.data, status=status.HTTP_200_OK)
            except:
                return JsonResponse({'Message': 'Error Invoice for this task does not exist'}, status=status.HTTP_400_BAD_REQUEST)
        return JsonResponse({'Message': 'Error you are not member of this case'}, status=status.HTTP_400_BAD_REQUEST)


class payment_status(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, payment_id):
        payment_entry = invoice_payment.objects.get(pk=payment_id)
        if request.user.id == payment_entry.invoice.task.task_case.created_by.id:
            payment_entry.status = True
            payment_entry.save()
            return JsonResponse({"Payment": "Status True, Payment Done"})
        return JsonResponse({"ERROR": "No Authorization"})


class payment_due_date(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, payment_id):
        payment_entry = invoice_payment.objects.get(pk=payment_id)
        if case_user_flag(payment_entry.invoice.task.task_case, request.user) or case_client_flag(payment_entry.invoice.task.task_case, request.user):
            serializer = invoice_payment_serializer(payment_entry)
            return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request, payment_id):
        payment_entry = invoice_payment.objects.get(pk=payment_id)

        if case_user_flag(payment_entry.invoice.task.task_case, request.user):
            invoice_entry = payment_entry.invoice
            all_payments = invoice_payment.objects.filter(invoice=invoice_entry)
            count = -1

            if invoice_entry.category != 'single':
                for element in all_payments:
                    if element == payment_entry:
                        break
                    else:
                        count = count + 1

                try:
                    datetime_object = datetime.strptime(request.data['due_date'], '%Y-%m-%d')
                except:
                    return JsonResponse({'Message': 'Error Due date must be in format %Y-%m-%d'}, status=status.HTTP_400_BAD_REQUEST)           # adding due_date
                if datetime_object.date() > date.today():
                    if count == -1 or (all_payments[count].due_date is not None and all_payments[count].due_date < datetime_object.date()):
                        payment_entry.due_date = datetime_object.date()
                        payment_entry.save()
                        serializer = invoice_payment_serializer(payment_entry)
                        return Response(serializer.data, status=status.HTTP_200_OK)
                    else:
                        return JsonResponse({'Message': 'Error Due date cannot be behind the previous payment due_date'}, status=status.HTTP_400_BAD_REQUEST)
                else:
                    return JsonResponse({'Message': 'Error due_date cannot be behind current date'}, status=status.HTTP_400_BAD_REQUEST)

            else:
                try:
                    datetime_object = datetime.strptime(request.data['due_date'], '%Y-%m-%d')
                except:
                    return JsonResponse({'Message': 'Error Due date must be in format %Y-%m-%d'}, status=status.HTTP_400_BAD_REQUEST)           # adding due_date
                if datetime_object.date() > date.today():
                    payment_entry.due_date = datetime_object.date()
                    payment_entry.save()
                    serializer = invoice_payment_serializer(payment_entry)
                    return Response(serializer.data, status=status.HTTP_200_OK)
                else:
                    return JsonResponse({'Message': 'Error due_date cannot be behind current date'}, status=status.HTTP_400_BAD_REQUEST)


class user_invoice(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        member_result = []
        client_result = []
        dict1 = {'member': {'paid': [], 'unpaid': []}, 'client': {'paid': [], 'unpaid': []}}
        case_set = request.user.case_members.all()
        for case_element in case_set:
            task_set = task.objects.filter(task_case=case_element)
            for task_element in task_set:
                try:
                    invoice_element = task_invoice.objects.get(task=task_element)
                    member_result.append(invoice_element)
                except:
                    pass

        for invoice_element in member_result:
            payment_set = invoice_payment.objects.filter(invoice=invoice_element)
            inv_serializer = task_invoice_serializer(invoice_element)
            pay_serializer = invoice_payment_serializer(payment_set, many=True)
            dict2 = inv_serializer.data
            dict2['payments'] = pay_serializer.data

            if len(payment_set) != 0:
                if payment_set[len(payment_set)-1].status:
                    dict1['member']['paid'].append(dict2)
                else:
                    dict1['member']['unpaid'].append(dict2)

        case_set = request.user.case_clients.all()
        for case_element in case_set:
            task_set = task.objects.filter(task_case=case_element)
            for task_element in task_set:
                try:
                    invoice_element = task_invoice.objects.get(task=task_element)
                    client_result.append(invoice_element)
                except:
                    pass

        for invoice_element in client_result:
            payment_set = invoice_payment.objects.filter(invoice=invoice_element)
            inv_serializer = task_invoice_serializer(invoice_element)
            pay_serializer = invoice_payment_serializer(payment_set, many=True)
            dict2 = inv_serializer.data
            dict2['payments'] = pay_serializer.data

            if len(payment_set) != 0:
                if payment_set[len(payment_set)-1].status:
                    dict1['client']['paid'].append(dict2)
                else:
                    dict1['client']['unpaid'].append(dict2)

        return JsonResponse(dict1, status=status.HTTP_200_OK)






