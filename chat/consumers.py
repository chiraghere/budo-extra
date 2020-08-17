import json
from asgiref.sync import async_to_sync
from channels.generic.websocket import WebsocketConsumer
from .models import *
from .serializer import message_serializer
from cases.models import *
from django.contrib.auth.models import User


class ChatConsumer(WebsocketConsumer):

    def show_previous_chats(self, new_chat):
        message_set = message.last_20(self, new_chat)
        serializer = message_serializer(message_set, many=True)
        content = {
            'message': serializer.data
        }
        return self.chat_message(content)

    def connect(self):
        self.room_name = self.scope['url_route']['kwargs']['room_name']
        self.room_group_name = 'chat_%s' % self.room_name

        # Join room group
        async_to_sync(self.channel_layer.group_add)(
            self.room_group_name,
            self.channel_name
        )

        self.accept()
        try:
            self.current_case = case.objects.get(pk=int(self.room_name))
            try:
                self.new_chat = chat.objects.get(case=self.current_case)
                self.show_previous_chats(self.new_chat)
            except:
                self.new_chat = chat.objects.create(case=self.current_case)
                self.new_chat.save()
        except:
            return self.chat_message({
            'message': 'no case exist'
        })

    def disconnect(self, close_code):
        # Leave room group
        async_to_sync(self.channel_layer.group_discard)(
            self.room_group_name,
            self.channel_name
        )

    # Receive message from WebSocket
    def receive(self, text_data):
        data = json.loads(text_data)
        new_message = data['message']
        new_user_id = data['user']
        user = User.objects.get(pk=new_user_id)
        print(user)

        obj = message.objects.create(content=new_message, chat=self.new_chat, created_by=user)
        obj.save()
        new_id = obj.id
        obj = message.objects.get(pk=new_id)
        serializer = message_serializer(obj)
        print(serializer.data)
        return self.send_message(serializer.data)

    def send_message(self, obj):
        async_to_sync(self.channel_layer.group_send)(
            self.room_group_name,
            {
                'type': 'chat_message',
                'message': obj
            }
        )

    # Receive message from room group
    def chat_message(self, event):
        message = event['message']

        # Send message to WebSocket
        self.send(text_data=json.dumps({
            'message': message
        }))


class UserConsumer(WebsocketConsumer):

    def show_previous_chats(self, new_chat):
        message_set = message.last_20(self, new_chat)
        serializer = message_serializer(message_set, many=True)
        content = {
            'message': serializer.data
        }
        return self.chat_message(content)

    def connect(self):
        self.room_name = self.scope['url_route']['kwargs']['room_name']
        self.room_group_name = 'chat_%s' % self.room_name

        # Join room group
        async_to_sync(self.channel_layer.group_add)(
            self.room_group_name,
            self.channel_name
        )
        self.accept()
        self.new_chat = chat.objects.get(channel_number=int(self.room_name))
        self.show_previous_chats(self.new_chat)

    def disconnect(self, close_code):
        # Leave room group
        async_to_sync(self.channel_layer.group_discard)(
            self.room_group_name,
            self.channel_name
        )

    # Receive message from WebSocket
    def receive(self, text_data):
        data = json.loads(text_data)
        new_message = data['message']
        new_user_id = data['user']
        user = User.objects.get(pk=new_user_id)

        obj = message.objects.create(content=new_message, chat=self.new_chat, created_by=user)
        obj.save()
        new_id = obj.id
        obj = message.objects.get(pk=new_id)
        serializer = message_serializer(obj)
        return self.send_message(serializer.data)

    def send_message(self, obj):
        async_to_sync(self.channel_layer.group_send)(
            self.room_group_name,
            {
                'type': 'chat_message',
                'message': obj
            }
        )

    # Receive message from room group
    def chat_message(self, event):
        message = event['message']

        # Send message to WebSocket
        self.send(text_data=json.dumps({
            'message': message
        }))


class GroupConsumer(WebsocketConsumer):

    def show_previous_chats(self, new_chat):
        message_set = message.last_20(self, new_chat)
        serializer = message_serializer(message_set, many=True)
        content = {
            'message': serializer.data
        }
        return self.chat_message(content)

    def connect(self):
        self.room_name = self.scope['url_route']['kwargs']['room_name']
        self.room_group_name = 'chat_%s' % self.room_name

        # Join room group
        async_to_sync(self.channel_layer.group_add)(
            self.room_group_name,
            self.channel_name
        )
        self.accept()
        self.new_chat = chat.objects.get(channel_number=self.room_name)
        self.show_previous_chats(self.new_chat)

    def disconnect(self, close_code):
        # Leave room group
        async_to_sync(self.channel_layer.group_discard)(
            self.room_group_name,
            self.channel_name
        )

    # Receive message from WebSocket
    def receive(self, text_data):
        data = json.loads(text_data)
        new_message = data['message']
        new_user_id = data['user']
        user = User.objects.get(pk=new_user_id)

        obj = message.objects.create(content=new_message, chat=self.new_chat, created_by=user)
        obj.save()
        new_id = obj.id
        obj = message.objects.get(pk=new_id)
        serializer = message_serializer(obj)
        return self.send_message(serializer.data)

    def send_message(self, obj):
        async_to_sync(self.channel_layer.group_send)(
            self.room_group_name,
            {
                'type': 'chat_message',
                'message': obj
            }
        )

    # Receive message from room group
    def chat_message(self, event):
        message = event['message']

        # Send message to WebSocket
        self.send(text_data=json.dumps({
            'message': message
        }))