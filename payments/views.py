from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.filters import OrderingFilter
from rest_framework.pagination import PageNumberPagination
from rest_framework import status, generics
from django.db import transaction
from django_filters.rest_framework import DjangoFilterBackend

from .models import Organization, Payment, BalanceLog
from .serializers import WebhookSerializer, BalanceSerializer, PaymentSerializer
from drf_spectacular.utils import (
    extend_schema,
    OpenApiParameter,
    OpenApiExample,
    OpenApiTypes,
)

import logging

logger = logging.getLogger('payments')

class BankWebhookView(APIView):
    """Прием платежных вебхуков"""
    @extend_schema(
        summary="Прием платежных вебхуков",
        description="""
        Принимает уведомления от банка о совершенных платежах.
        При первом получении начисляет сумму на баланс организации.
        """,
        request={
            'application/json': {
                'example': {
                    "operation_id": "ccf0a86d-041b-4991-bcf7-e2352f7b8a4a",
                    "amount": 145000,
                    "payer_inn": "1234567890",
                    "document_number": "PAY-328",
                    "document_date": "2024-04-27T21:00:00Z"
                }
            }
        },
        responses={
            200: None,
            400: OpenApiTypes.OBJECT,
            500: OpenApiTypes.OBJECT
        },
        examples=[
            OpenApiExample(
                'Пример платежа',
                value={
                    "operation_id": "ccf0a86d-041b-4991-bcf7-e2352f7b8a4a",
                    "amount": 145000,
                    "payer_inn": "1234567890",
                    "document_number": "PAY-328",
                    "document_date": "2024-04-27T21:00:00Z"
                },
                request_only=True
            )
        ]
    )
    def post(self, request):
        serializer = WebhookSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        data = serializer.validated_data
        operation_id = data['operation_id']
        
        if Payment.objects.filter(operation_id=operation_id).exists():
            return Response(status=status.HTTP_200_OK)
        
        try:
            with transaction.atomic():
                logger.info(f"Обрабатывается платеж {operation_id}")
                
                organization, created = Organization.objects.get_or_create(
                    inn=data['payer_inn'],
                    defaults={'balance': 0}
                )
                
                payment = Payment.objects.create(
                    operation_id=operation_id,
                    amount=data['amount'],
                    payer_inn=data['payer_inn'],
                    document_number=data['document_number'],
                    document_date=data['document_date'],
                    organization=organization
                )
                
                organization.balance += data['amount']
                organization.save()
                
                BalanceLog.objects.create(
                    organization=organization,
                    amount=data['amount'],
                    new_balance=organization.balance,
                    payment=payment
                )
                
                logger.info(
                    f"Начислен платеж {operation_id} на сумму {data['amount']} "
                    f"для организации ИНН {data['payer_inn']}. "
                    f"Новый баланс: {organization.balance}",
                    extra={
                        'operation_id': operation_id,
                        'amount': data['amount'],
                        'inn': data['payer_inn'],
                        'new_balance': organization.balance
                    }
                )
                
            return Response(status=status.HTTP_200_OK)
        
        except Exception as e:
            logger.error(
                f"Ошибка при обработке платежа {operation_id}: {str(e)}",
                exc_info=True,
                extra={'request_data': request.data}
            )
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class OrganizationBalanceView(APIView):
    """Получение баланса организации"""
    @extend_schema(
        summary="Получение баланса организации",
        description="Возвращает текущий баланс организации по ИНН",
        parameters=[
            OpenApiParameter(
                name='inn',
                type=OpenApiTypes.STR,
                location=OpenApiParameter.PATH,
                description='ИНН организации (10 или 12 цифр)'
            )
        ],
        responses={
            200: {
                'type': 'object',
                'examples': {
                    'application/json': {
                        "inn": "1234567890",
                        "balance": 145000
                    }
                }
            },
            404: OpenApiTypes.OBJECT
        }
    )
    def get(self, request, inn):
        try:
            logger.info(f"Получение баланса для организации ИНН {inn}")
            
            organization = Organization.objects.get(inn=inn)
            serializer = BalanceSerializer(organization)
            
            logger.info(f"Баланс для организации ИНН {inn}: {serializer.data['balance']}")
            
            return Response(serializer.data)
        
        except Organization.DoesNotExist:
            logger.error(f"Организация с ИНН {inn} не найдена")
            
            return Response(
                {'error': 'Organization not found'},
                status=status.HTTP_404_NOT_FOUND
            )
            
            
class OrganizationPaymentsView(generics.ListAPIView):
    """Список платежей организации"""
    serializer_class = PaymentSerializer
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_fields = ['document_number', 'document_date']
    ordering_fields = ['amount', 'document_date', 'created_at']
    ordering = ['-document_date']
    @extend_schema(
        summary="Список платежей организации",
        description="Возвращает список платежей организации с возможностью фильтрации и сортировки",
        responses={
            200: PaymentSerializer(many=True),
            400: OpenApiTypes.OBJECT
        },
        examples=[
            OpenApiExample(
                'Пример ответа',
                value=[{
                    "operation_id": "ccf0a86d-041b-4991-bcf7-e2352f7b8a4a",
                    "amount": 145000,
                    "payer_inn": "1234567890",
                    "document_number": "PAY-328",
                    "document_date": "2024-04-27T21:00:00Z",
                        "created_at": "2024-04-27T21:05:00Z"
                }],
                response_only=True
            )
        ],
        parameters=[
            OpenApiParameter(
                name='payer_inn',
                type=OpenApiTypes.STR,
                location=OpenApiParameter.QUERY,
                description='Фильтр по ИНН организации'
            ),
            OpenApiParameter(
                name='document_number',
                type=OpenApiTypes.STR,
                location=OpenApiParameter.QUERY,
                description='Фильтр по номеру документа'
            ),
            OpenApiParameter(
                name='ordering',
                type=OpenApiTypes.STR,
                location=OpenApiParameter.QUERY,
                description='Поле для сортировки (prefix "-" для DESC)'
            ),
        ]
    )
    def get_queryset(self):
        try:
            logger.info("Получение списка платежей")
            
            queryset = Payment.objects.all()
            payer_inn = self.request.query_params.get('payer_inn')
            if payer_inn:
                queryset = queryset.filter(payer_inn=payer_inn)
            
            logger.info(f"Найдено {queryset.count()} платежей")
            return queryset
        except Exception as e:
            logger.error(f"Ошибка при получении списка платежей: {str(e)}")
            
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )