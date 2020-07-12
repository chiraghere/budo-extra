from django.urls import path
from .views import *
from rest_framework.authtoken import views as tokenviews

urlpatterns = [
    path('add_case/', create_Case.as_view(), name='new_case'),
    path('show_cases_as_member/', show_cases_as_member.as_view(), name='show_cases_as_member'),
    path('show_cases_as_client/', show_cases_as_client.as_view(), name='show_cases_as_client'),
    path('show_case/<int:case_id>/', show_case.as_view(), name='show_case'),
    path('case_members/<int:case_id>/', case_assign_members.as_view(), name='case_members'),
    path('case_clients/<int:case_id>/', case_assign_clients.as_view(), name='case_clients'),
    path('add_task/<int:case_id>/', add_task.as_view(), name='add_task'),
    path('task_members/<int:task_id>/', add_task_members.as_view(), name='add_task_members'),
    path('show_task/<int:task_id>/', show_task_complete.as_view(), name='task_complete'),
    path('task_details/<int:task_id>/', add_task_details.as_view(), name='add_task_details'),
    path('task_comment/<int:task_id>/', add_task_comment.as_view(), name='add_task_comment'),
    path('edit_task_comment/<int:comment_id>/', edit_task_comment.as_view(), name='edit_task_comment'),
    path('task_checklist/<int:task_id>/', add_task_checklist.as_view(), name='add_task_checklist'),
    path('edit_task_checklist/<int:checklist_id>/', edit_task_checklist.as_view(), name='edit_task_checklist'),
    path('task_checklist_items/<int:checklist_id>/', add_task_checklist_items.as_view(), name='add_task_checklist_items'),
    path('edit_checklist_items/<int:checklist_id>/', edit_checklist_items.as_view(), name='edit_task_checklist_items'),
    path('task_label/<int:task_id>/', add_task_label.as_view(), name='add_task_label'),
    path('edit_task_label/<int:label_id>', delete_task_labels.as_view(), name='delete_task_label'),
    path('task_due_date/<int:task_id>/', add_due_date.as_view(), name='add_task_due_date'),
    path('task_timer/<int:task_id>/<str:action>/', task_timer.as_view(), name='add_task_timer'),
    path('task_image/<int:task_id>/', Image.as_view(), name='add_task_image'),
    path('task_document/<int:task_id>/', Document.as_view(), name='add_task_document'),
    path('task_billing_type/<int:task_id>/', task_billing_type.as_view(), name='task_billing_type'),
    path('task_cost/<int:task_id>/', add_task_cost.as_view(), name='add_task_cost'),
    path('show_case_activity/<int:case_id>/', show_case_activity.as_view(), name='show_case_activity'),
]
