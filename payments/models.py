from django.db import models
from django.core.validators import MinValueValidator, MinLengthValidator

class Organization(models.Model):
    """Организация, для которой обрабатываются платежи"""
    inn = models.CharField(validators=[MinLengthValidator(10)], verbose_name='ИНН', max_length=12, unique=True, help_text='ИНН организации')
    balance = models.DecimalField(
        verbose_name='Баланс',
        help_text='Сумма на балансе организации',
        max_digits=15, 
        decimal_places=2, 
        default=0,
        validators=[MinValueValidator(0)],
    )
    
    class Meta:
        verbose_name = 'Организация'
        verbose_name_plural = 'Организации'
        indexes = [
            models.Index(fields=['inn']),
        ]
    
    def __str__(self):
        return f'Организация ИНН {self.inn}'


class Payment(models.Model):
    """Платеж, созданный при получении уведомления от банка"""
    operation_id = models.UUIDField(unique=True, verbose_name='ID операции')
    amount = models.DecimalField(
        max_digits=15, 
        decimal_places=2, 
        validators=[MinValueValidator(0)],
        verbose_name='Сумма',
        help_text='Сумма платежа'
    )
    payer_inn = models.CharField(max_length=12, verbose_name='ИНН плательщика', help_text='ИНН плательщика')
    document_number = models.CharField(max_length=50, verbose_name='Номер документа', help_text='Номер документа')
    document_date = models.DateTimeField(verbose_name='Дата документа', help_text='Дата документа')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Дата создания', help_text='Дата создания')
    
    organization = models.ForeignKey(
        Organization,
        on_delete=models.CASCADE,
        related_name='payments',
        null=True,
        blank=True
    )
    
    class Meta:
        verbose_name = 'Платеж'
        verbose_name_plural = 'Платежи'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['operation_id']),
        ]
    

    def __str__(self):
        return f'Платеж {self.operation_id} на сумму {self.amount}'
    

class BalanceLog(models.Model):
    """Лог изменения баланса организации"""
    organization = models.ForeignKey(
        Organization, 
        on_delete=models.CASCADE,
        related_name='balance_logs',
        verbose_name='Организация',
        help_text='Организация, для которой изменяется баланс'
    )
    amount = models.DecimalField(
        max_digits=15, 
        decimal_places=2,
        verbose_name='Сумма изменения',
        help_text='Сумма, на которую изменяется баланс'
    )
    new_balance = models.DecimalField(
        max_digits=15, 
        decimal_places=2,
        verbose_name='Новый баланс',
        help_text='Новый баланс организации'
    )
    payment = models.ForeignKey(
        Payment,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name='Платеж',
        help_text='Платеж, который привел к изменению баланса'
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Дата изменения', help_text='Дата изменения баланса')
    
    class Meta:
        verbose_name = 'Лог баланса'
        verbose_name_plural = 'Логи баланса'
        ordering = ['-created_at']
    
    def __str__(self):
        return f'Изменение баланса для {self.organization.inn} на {self.amount}'