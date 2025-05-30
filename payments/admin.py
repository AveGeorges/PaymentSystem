from django.contrib import admin
from .models import Organization, Payment, BalanceLog

@admin.register(Organization)
class OrganizationAdmin(admin.ModelAdmin):
    """Организация, для которой обрабатываются платежи"""
    list_display = ('inn', 'balance', 'payments_count')
    search_fields = ('inn',)
    list_filter = ('balance',)
    ordering = ('inn',)
    
    def payments_count(self, obj):
        return obj.payments.count()
    payments_count.short_description = 'Кол-во платежей'

@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    """Платеж, созданный при получении уведомления от банка"""
    list_display = ('operation_id', 'amount', 'payer_inn', 'document_number', 'document_date')
    list_filter = ('document_date', 'payer_inn')
    search_fields = ('operation_id', 'payer_inn', 'document_number')
    date_hierarchy = 'document_date'
    readonly_fields = ('operation_id', 'created_at')

@admin.register(BalanceLog)
class BalanceLogAdmin(admin.ModelAdmin):
    """Лог изменения баланса организации"""
    list_display = ('organization', 'amount', 'new_balance', 'created_at', 'payment_link')
    list_filter = ('created_at', 'organization')
    search_fields = ('organization__inn', 'payment__operation_id')
    date_hierarchy = 'created_at'
    readonly_fields = ('created_at', 'organization', 'amount', 'new_balance', 'payment')
    
    def payment_link(self, obj):
        if obj.payment:
            return f'<a href="/admin/payments/payment/{obj.payment.id}/change/">{obj.payment.operation_id}</a>'
        return '-'
    payment_link.short_description = 'Платеж'
    payment_link.allow_tags = True

admin.site.site_header = 'Панель управления платежной системой'
admin.site.site_title = 'Платежная система'
admin.site.index_title = 'Администрирование системы'