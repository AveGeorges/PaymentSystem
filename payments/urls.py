from django.urls import path
from rest_framework import routers
from .views import BankWebhookView, OrganizationBalanceView, OrganizationPaymentsView


urlpatterns = [
    path('api/webhook/bank/', BankWebhookView.as_view(), name='bank-webhook'),
    path('api/organizations/<str:inn>/balance/', OrganizationBalanceView.as_view(), name='organization-balance'),
    path('api/payments/', OrganizationPaymentsView.as_view(), name='organization-payments')
]