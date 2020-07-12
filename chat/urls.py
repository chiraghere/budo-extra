from django.urls import path

from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('cases/<str:case_id>/', views.case_room_auth.as_view(), name='case_auth_room'),
    path('user/new_channel/<int:user_id>/', views.new_user_room.as_view(), name='user_room'),
    path('user/<str:room_name>/', views.existing_user_room.as_view(), name='existing_user_room'),
    path('groups/new_channel/', views.new_group_room.as_view(), name='new_group'),
    path('groups/room/<str:room_name>/', views.existing_group_room.as_view(), name='existing_group'),
    path('groups/members/<str:room_name>/', views.group_members.as_view(), name='group_members'),
    path('groups/members/admin/<str:room_name>/', views.group_admin.as_view(), name='group_members_admin'),
]