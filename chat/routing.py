from django.urls import re_path

from . import consumers

websocket_urlpatterns = [
    re_path(r"ws/chat/cases/(?P<room_name>\w+)/$", consumers.ChatConsumer),
    re_path(r"ws/chat/user/(?P<room_name>\w+)/$", consumers.UserConsumer),
    re_path(r"ws/chat/groups/(?P<room_name>\w+)/$", consumers.GroupConsumer),
]