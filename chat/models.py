from django.db import models
from django.contrib.auth.models import User
from cases.models import case


class chat(models.Model):
    case = models.OneToOneField(case, on_delete=models.CASCADE, null=True)
    chat_name = models.CharField(max_length=16, null=True)
    chat_members = models.ManyToManyField(User, related_name='chat_members')
    channel_number = models.CharField(max_length=64, null=True, unique=True)
    chat_admin = models.ManyToManyField(User, related_name='chat_admin')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.case.case_name


class message(models.Model):
    content = models.TextField()
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, null=True)
    chat = models.ForeignKey(chat, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.content

    def last_20(self, current_chat):
        return message.objects.order_by('-created_at').filter(chat=current_chat)[:20]


class message_files(models.Model):
    docx = models.FileField(null=True)
    image = models.ImageField(null=True)
    audio = models.FileField(null=True)
    message = models.ForeignKey(message, on_delete=models.CASCADE)
# Create your models here.
