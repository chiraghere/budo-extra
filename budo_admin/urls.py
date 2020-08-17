from django.urls import path
from .views import *

urlpatterns = [
    path('admin_login/', admin_login.as_view(), name='admin_login'),
    path('admin_logout/', admin_logout.as_view(), name='admin_logout'),
    path('get_user_profile/', get_user_profile.as_view(), name='get_user_profile'),
    path('all_users/', all_users.as_view(), name='all_users'),
    path('get_user/<str:user_id>/', get_user.as_view(), name='get_user'),
    path('subscription/', subscription_view.as_view(), name='subscription'),
    path('add_subscription/', add_subscription.as_view(), name='add_subscription'),
    path('get_subscription/<int:sub_id>/', get_subscription.as_view(), name='get_subscription'),
    path('all_cases/', all_cases.as_view(), name='all_cases'),
    path('get_case/<int:case_id>/', get_case.as_view(), name='get_case'),
    path('dashboard/', dashboard.as_view(), name='dashboard'),
    path('revenue/', revenue.as_view(), name='revenue'),
]