from django.contrib import admin
from .models import FeeCategory, FeeStructure, FeeInstallment, StudentFeePayment

class FeeInstallmentInline(admin.TabularInline):
    model = FeeInstallment
    extra = 1

@admin.register(FeeCategory)
class FeeCategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'fee_type')
    list_filter = ('fee_type',)

@admin.register(FeeStructure)
class FeeStructureAdmin(admin.ModelAdmin):
    list_display = ('title', 'category', 'school_class', 'grade', 'academic_year', 'total_amount')
    list_filter = ('category', 'academic_year', 'grade')
    inlines = [FeeInstallmentInline]

@admin.register(FeeInstallment)
class FeeInstallmentAdmin(admin.ModelAdmin):
    list_display = ('fee_structure', 'title', 'installment_number', 'amount', 'due_date', 'is_current_due', 'requires_vehicle')
    list_filter = ('is_current_due', 'requires_vehicle', 'fee_structure__category')
    search_fields = ('title', 'fee_structure__title')

@admin.register(StudentFeePayment)
class StudentFeePaymentAdmin(admin.ModelAdmin):
    list_display = ('receipt_number', 'student', 'installment', 'amount_paid', 'payment_date', 'payment_mode', 'collected_by')
    list_filter = ('payment_mode', 'payment_date', 'installment__fee_structure')
    search_fields = ('receipt_number', 'student__full_name', 'student__admission_number', 'transaction_id')
