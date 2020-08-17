from django.urls import path
from .views import *
from rest_framework_swagger.views import get_swagger_view
from rest_framework.authtoken import views as tokenviews

schema_view = get_swagger_view(title='BUDO')

urlpatterns = [
    path('budo_docs/', schema_view),
    path('register/', UserCreate.as_view(), name='register'),
    path('login/', Userlogin.as_view(), name='login'),
    # path('verify_account/<str:flag>/', verify_account.as_view(), name='verify_account'),
    path('edit_account/', edit_account.as_view(), name='edit_account'),
    path('edit_password/', edit_password.as_view(), name='edit_password'),
    path('profile/', your_profile.as_view(), name='your_profile'),
    path('profile_status/<str:action>/', profile_status.as_view(), name='profile_status'),
    path('show_profile/<int:user_id>/', other_person_profile.as_view(), name='other_person_profile'),
    path('show_invite/', show_invite.as_view(), name='show_invite'),
    path('invite_decision/<int:invite_id>/', invite_decision.as_view(), name='invite_decision'),
    path('search/', search.as_view(), name='search'),
    path('view_subscriptions/', view_subscriptions.as_view(), name='subscriptions'),
    path('avail_subscriptions/<int:sub_id>/', avail_subscriptions.as_view(), name='avail_subscriptions'),
    path('subscriptions/', view_your_subscription.as_view(), name='subscriptions'),
]