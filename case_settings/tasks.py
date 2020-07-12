from celery import shared_task
import time
from cases.models import *
from cases.serializers import *
from datetime import datetime
from chat.models import *
from chat.serializer import *
import json
import zipfile
from chat.views import *
import os
from django.core.mail import send_mail, EmailMessage
from .views import *


@shared_task()
def sleepy(duration):
    time.sleep(duration)
    return None


@shared_task()
def send_case_email(case_id):
    time.sleep(10)

    zip1 = zipfile.ZipFile('zip/case.zip', 'w')
    get_case_chat_info(case_id, zip1)
    get_case_task_info(case_id, zip1)
    get_all_img(case_id, zip1)
    get_all_docs(case_id, zip1)

    zip1.close()

    email = EmailMessage(
        'Hello',
        'Case Details',
        'chiragsharma1061@gmail.com',
        ['chirag2214@outlook.com'],
    )

    email.attach_file('zip/case.zip')

    email.send()
