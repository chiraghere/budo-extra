from django.shortcuts import render
from django.http import HttpResponse
from django.http import JsonResponse
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.contrib.auth.models import User
from cases.models import *
from cases.serializers import *
from datetime import datetime
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


def get_all_docs(case_id, zip1):
    current_case = case.objects.get(pk=case_id)
    try:
        folder_path = 'media/media/' + str(current_case.case_name) + '/documents/'
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
        folder_path = 'media/media/' + str(current_case.case_name) + '/images/'
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


def invoice_category(request, invoice_obj, new_cost):
    if invoice_obj.category == 'single':
        payment = invoice_payment.objects.create(invoice=invoice_obj, payment=new_cost)
        payment.save()
    elif invoice_obj.category == 'equal':
        payment_cost = new_cost / int(invoice_obj.frequency)
        for loop in range(0, int(invoice_obj.frequency)):
            payment = invoice_payment.objects.create(invoice=invoice_obj, payment=payment_cost)
            payment.save()
    elif invoice_obj.category == 'unequal':
        for loop in range(0, int(request.data['frequency'])):
            payment = invoice_payment.objects.create(invoice=invoice_obj)
            payment.save()


class task_invoice_view(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, task_id):
        current_task = task.objects.get(pk=task_id)

        if request.user.id == current_task.task_case.created_by.id:

            timer_set = timer.objects.filter(task=current_task)

            if current_task.invoice_type == 'hourly' and timer_set[len(timer_set) - 1].status == 'end':
                time_diff = 0
                for interval in timer_set:
                    value = interval.start_time - interval.end_time
                    time_diff = time_diff - float(value.seconds) / 3600 - float(value.days) * 24

                total_cost = float(current_task.cost) * time_diff

                invoice = task_invoice.objects.create(task=current_task, total_cost=total_cost)
                invoice.save()
                invoice_id = invoice.id

                invoice_category(request, invoice, invoice.total_cost)

                queryset = task_invoice.objects.get(pk=invoice_id)
                serializer = task_invoice_serializer(queryset)
                return Response(serializer.data, status=status.HTTP_201_CREATED)

            elif current_task.invoice_type == 'onetime':
                invoice = task_invoice.objects.create(task=current_task, total_cost=current_task.cost)
                invoice.save()
                invoice_id = invoice.id

                invoice_category(request, invoice, invoice.total_cost)

                queryset = task_invoice.objects.get(pk=invoice_id)
                serializer = task_invoice_serializer(queryset)
                return Response(serializer.data, status=status.HTTP_201_CREATED)

            else:
                return JsonResponse({
                    "Error": "Either Timer is still active OR some task details are missing(Eg : invoice_type or cost "})
        else:
            return JsonResponse({"Error": "you are not a member of this case"})


class show_invoice(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, task_id):
        current_task = task.objects.get(pk=task_id)
        if case_user_flag(current_task.task_case, request.user) or case_client_flag(current_task.task_case,
                                                                                    request.user):
            result = []
            try:
                task_invoice_set = task_invoice.objects.get(task=current_task)
                payment_set = invoice_payment.objects.filter(invoice=task_invoice_set)
                serializer = task_invoice_serializer(task_invoice_set)
                payment_serializer = invoice_payment_serializer(payment_set, many=True)
                json = {'Invoice': serializer.data, 'Payments': payment_serializer.data}
                result.append(json)
                return JsonResponse(result, safe=False)
            except:
                return JsonResponse({"ERROR": "No Invoice Exists"})
        else:
            return JsonResponse({"Error": "you are not a member of this case"})

    def delete(self, request, task_id):
        current_task = task.objects.get(pk=task_id)
        if request.user.id == current_task.task_case.created_by.id:
            task_invoice_set = task_invoice.objects.get(task=current_task)
            task_invoice_set.delete()
            return JsonResponse({"Invoice": "Deleted"})


class invoice_payment_set(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, task_id):
        current_task = task.objects.get(pk=task_id)
        current_invoice = task_invoice.objects.get(task=current_task)

        payment_entry_set = invoice_payment.objects.filter(invoice=current_invoice)

        serializer = invoice_payment_serializer(payment_entry_set, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request, task_id):
        current_task = task.objects.get(pk=task_id)
        current_invoice = task_invoice.objects.get(task=current_task)

        payment_entry_set = invoice_payment.objects.filter(invoice=current_invoice)
        remaining_payment = float(current_invoice.total_cost)
        completed_frequencies = 0

        if request.data['category'] == 'single' and request.data['frequency'] > 1:
            return JsonResponse({"ERROR": "Category single cannot have frequency more than 1"})

        if request.data['category'] != current_invoice.category or request.data['frequency'] != current_invoice.frequency:
            for element in payment_entry_set:
                if element.status:
                    remaining_payment = remaining_payment - element.payment
                    completed_frequencies = completed_frequencies + 1
                else:
                    element.delete()

                if request.data['category'] != current_invoice.category:
                    current_invoice.category = request.data['category']
                    current_invoice.save()

                if request.data['frequency'] != current_invoice.frequency:
                    if completed_frequencies <= request.data['frequency']:
                        current_invoice.frequency = request.data['frequency']
                        current_invoice.save()

                invoice_category(request, current_invoice, remaining_payment)

            return JsonResponse({"Payments Model": "Updated"})
        return JsonResponse({"Payments Model": "No Change"})


class payment_status(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, payment_id):
        payment_entry = invoice_payment.objects.get(pk=payment_id)
        if request.user.id == payment_entry.invoice.task.task_case.created_by.id:
            payment_entry.status = True
            return JsonResponse({"Payment": "Status True, Payment Done"})
        return JsonResponse({"ERROR": "No Authorization"})


class payment_due_date(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, task_id):
        current_task = task.objects.get(pk=task_id)
        current_invoice = task_invoice.objects.get(task=current_task)

        payment_set = invoice_payment.objects.filter(invoice=current_invoice)

        try:
            for (entry, due_date) in zip(payment_set, request.data['due_date']):
                entry.due_date = due_date
                entry.save()
        except:
            return JsonResponse({"ERROR": "You entered more due dates than frequencies"})

        return JsonResponse({"Payment": "due_date added"})





