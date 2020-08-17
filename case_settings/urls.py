from django.urls import path
from .views import *

urlpatterns = [
    path('get_all_case_info/<int:case_id>/', get_all_case_info.as_view(), name='get_all_case_info'),
    path('task_invoice/<int:task_id>/', task_invoice_view.as_view(), name='task_invoice'),
    path('invoice_payment_set/<int:task_id>/', invoice_payment_set.as_view(), name='invoice_payments'),
    path('invoice_payment_paid/<int:payment_id>/', payment_status.as_view(), name='payment_status'),
    path('invoice_payment/<int:payment_id>/', payment_due_date.as_view(), name='payment_due_date'),
    path('invoices/', user_invoice.as_view(), name='invoice'),
    ]