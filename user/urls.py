from django.urls import path
from .views import *
from rest_framework.authtoken import views as tokenviews

urlpatterns = [
    path('register/', UserCreate.as_view(), name='register'),
    path('login/', Userlogin.as_view(), name='login'),
    path('profile/', your_profile.as_view(), name='your_profile'),
    path('profile_status/<str:action>/', profile_status.as_view(), name='profile_status'),
    path('show_profile/<int:user_id>/', other_person_profile.as_view(), name='other_person_profile'),
    path('show_invite/', show_invite.as_view(), name='show_invite'),
    path('invite_decision/<int:invite_id>/', invite_decision.as_view(), name='invite_decision'),
    path('search/', search.as_view(), name='search'),
]