from rest_framework import serializers
from .models import Organization, Payment
from django.core.validators import MinLengthValidator

class WebhookSerializer(serializers.Serializer):
    """Сериализатор для приема платежных вебхуков"""
    operation_id = serializers.UUIDField()
    amount = serializers.DecimalField(max_digits=15, decimal_places=2, min_value=0)
    payer_inn = serializers.CharField(
        max_length=12,
        validators=[MinLengthValidator(10)]
    )
    document_number = serializers.CharField(max_length=50)
    document_date = serializers.DateTimeField()

    def validate_payer_inn(self, value):
        if not value.isdigit():
            raise serializers.ValidationError("ИНН должен содержать только цифры")
        return value


class BalanceSerializer(serializers.ModelSerializer):
    """Сериализатор для получения баланса организации"""
    class Meta:
        model = Organization
        fields = ['inn', 'balance']
        
        
class PaymentSerializer(serializers.ModelSerializer):
    """Сериализатор для получения платежа"""
    class Meta:
        model = Payment
        fields = [
            'operation_id', 
            'amount', 
            'payer_inn', 
            'document_number', 
            'document_date', 
            'created_at'
        ]