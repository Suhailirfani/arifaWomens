from django import forms
from .models import (
    FeeCategory, FeeStructure, FeeInstallment, StudentFeePayment,
    BusStop, StudentVehiclePass, VehicleBillingSetting, StudentMonthlyVehicleFee
)
from students.models import Student
import uuid
from datetime import date
from decimal import Decimal


class FeePaymentForm(forms.ModelForm):
    class Meta:
        model = StudentFeePayment
        fields = [
            'student', 'fee_type', 'installment', 'monthly_vehicle_fee', 'amount_paid', 'payment_date',
            'payment_mode', 'transaction_id', 'receipt_number', 'remarks'
        ]
        widgets = {
            'student': forms.Select(attrs={'class': 'form-select', 'id': 'select-student'}),
            'fee_type': forms.Select(attrs={'class': 'form-select', 'id': 'select-fee-type'}),
            'installment': forms.Select(attrs={'class': 'form-select', 'id': 'select-installment'}),
            'monthly_vehicle_fee': forms.Select(attrs={'class': 'form-select', 'id': 'select-vehicle-fee'}),
            'amount_paid': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'id': 'input-amount-paid'}),
            'payment_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'payment_mode': forms.Select(attrs={'class': 'form-select'}),
            'transaction_id': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'UTR / Cheque / Ref Number'}),
            'receipt_number': forms.TextInput(attrs={'class': 'form-control', 'readonly': 'readonly'}),
            'remarks': forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'placeholder': 'Optional payment notes'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['installment'].required = False
        self.fields['monthly_vehicle_fee'].required = False

        if not self.instance.pk and not self.initial.get('receipt_number'):
            # Auto generate receipt number
            year = date.today().year
            rand_suffix = str(uuid.uuid4().int)[:5]
            self.initial['receipt_number'] = f"REC-{year}-{rand_suffix}"
            self.initial['payment_date'] = date.today()

    def clean(self):
        cleaned_data = super().clean()
        fee_type = cleaned_data.get('fee_type')
        installment = cleaned_data.get('installment')
        vehicle_fee = cleaned_data.get('monthly_vehicle_fee')

        if fee_type == StudentFeePayment.FeeType.INSTALLMENT and not installment:
            self.add_error('installment', 'Please select an installment to collect course fees against.')
        elif fee_type == StudentFeePayment.FeeType.VEHICLE_MONTHLY and not vehicle_fee:
            self.add_error('monthly_vehicle_fee', 'Please select the monthly vehicle fee record.')

        return cleaned_data


class FeeCategoryForm(forms.ModelForm):
    class Meta:
        model = FeeCategory
        fields = ['name', 'fee_type', 'description']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. Course Fee (Installments)'}),
            'fee_type': forms.Select(attrs={'class': 'form-select'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'placeholder': 'Optional description'}),
        }


class FeeStructureForm(forms.ModelForm):
    class Meta:
        model = FeeStructure
        fields = ['title', 'category', 'school_class', 'grade', 'academic_year', 'total_amount', 'description']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. Plus One Humanities - Annual Course Fee'}),
            'category': forms.Select(attrs={'class': 'form-select'}),
            'school_class': forms.Select(attrs={'class': 'form-select'}),
            'grade': forms.Select(attrs={'class': 'form-select'}),
            'academic_year': forms.Select(attrs={'class': 'form-select'}),
            'total_amount': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'placeholder': '0.00'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'placeholder': 'Optional notes or guidelines'}),
        }


class FeeInstallmentForm(forms.ModelForm):
    class Meta:
        model = FeeInstallment
        fields = [
            'fee_structure', 'title', 'installment_number', 'amount',
            'due_date', 'is_current_due', 'requires_vehicle', 'month', 'year'
        ]
        widgets = {
            'fee_structure': forms.Select(attrs={'class': 'form-select'}),
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. 1st Installment (Term 1 / Admission)'}),
            'installment_number': forms.NumberInput(attrs={'class': 'form-control', 'min': 1}),
            'amount': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'placeholder': '0.00'}),
            'due_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'is_current_due': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'requires_vehicle': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'month': forms.NumberInput(attrs={'class': 'form-control', 'min': 1, 'max': 12, 'placeholder': 'Month (1-12, optional)'}),
            'year': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Year (optional)'}),
        }


class BusStopForm(forms.ModelForm):
    class Meta:
        model = BusStop
        fields = ['stop_name', 'route_name', 'monthly_fee', 'pickup_time', 'drop_time', 'is_active']
        widgets = {
            'stop_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. Feroke Chungam, Ramanattukara'}),
            'route_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. Route 1 - Feroke / Pantheerankavu'}),
            'monthly_fee': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'placeholder': 'e.g. 1200.00'}),
            'pickup_time': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. 07:45 AM'}),
            'drop_time': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. 04:30 PM'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


class StudentVehiclePassForm(forms.ModelForm):
    class Meta:
        model = StudentVehiclePass
        fields = ['student', 'bus_stop', 'discount_type', 'discount_value', 'discount_reason', 'is_active', 'start_date']
        widgets = {
            'student': forms.Select(attrs={'class': 'form-select', 'id': 'select-pass-student'}),
            'bus_stop': forms.Select(attrs={'class': 'form-select', 'id': 'select-pass-stop'}),
            'discount_type': forms.Select(attrs={'class': 'form-select', 'id': 'select-discount-type'}),
            'discount_value': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'id': 'input-discount-val', 'placeholder': '0.00'}),
            'discount_reason': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. One-way travel only, Sibling concession'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'start_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
        }


class StudentMonthlyVehicleFeeCustomForm(forms.ModelForm):
    """
    Form allowing Admin to customize vehicle fee for a specific month for partial usage:
    - Reducing exact amount (₹)
    - Reducing percentage (%)
    - Custom reason / notes
    """
    class Meta:
        model = StudentMonthlyVehicleFee
        fields = ['custom_discount_type', 'custom_discount_value', 'custom_notes', 'final_amount', 'due_date']
        widgets = {
            'custom_discount_type': forms.Select(attrs={'class': 'form-select', 'id': 'id_custom_discount_type'}),
            'custom_discount_value': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'id': 'id_custom_discount_value', 'placeholder': '0.00'}),
            'custom_notes': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. Partial month usage (10 days only), medical leave'}),
            'final_amount': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'id': 'id_final_amount'}),
            'due_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['final_amount'].required = False
        self.fields['custom_notes'].required = False
        self.fields['custom_discount_value'].required = False


class VehicleBillingSettingForm(forms.ModelForm):
    class Meta:
        model = VehicleBillingSetting
        fields = ['due_day_of_month', 'auto_generate', 'academic_months']
        widgets = {
            'due_day_of_month': forms.NumberInput(attrs={'class': 'form-control', 'min': 1, 'max': 31, 'placeholder': '1'}),
            'auto_generate': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'academic_months': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. 6,7,8,9,10,11,12,1,2,3'}),
        }

