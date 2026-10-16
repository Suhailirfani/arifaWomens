from django import forms
from .models import Student
from academics.models import SchoolClass, AcademicYear

class StudentForm(forms.ModelForm):
    class Meta:
        model = Student
        fields = [
            'admission_number', 'roll_number', 'full_name', 'current_class', 'academic_year',
            'date_of_birth', 'gender', 'blood_group', 'father_or_guardian_name', 'mother_name',
            'guardian_phone', 'guardian_email', 'guardian_occupation', 'address',
            'vehicle_opted', 'vehicle_route', 'admission_date', 'photo', 'is_active'
        ]
        widgets = {
            'admission_number': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. ARF-2026-001'}),
            'roll_number': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. 01'}),
            'full_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Full Name'}),
            'current_class': forms.Select(attrs={'class': 'form-select'}),
            'academic_year': forms.Select(attrs={'class': 'form-select'}),
            'date_of_birth': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'gender': forms.Select(attrs={'class': 'form-select'}),
            'blood_group': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. B+, O+'}),
            'father_or_guardian_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Guardian Name'}),
            'mother_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Mother Name (Optional)'}),
            'guardian_phone': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Phone Number'}),
            'guardian_email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Email Address'}),
            'guardian_occupation': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Occupation'}),
            'address': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Residential Address'}),
            'vehicle_opted': forms.CheckboxInput(attrs={'class': 'form-check-input', 'id': 'id_vehicle_opted'}),
            'vehicle_route': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. Feroke Route, Kodampuzha Route'}),
            'admission_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


class BulkUploadForm(forms.Form):
    excel_file = forms.FileField(
        widget=forms.FileInput(attrs={'class': 'form-control', 'accept': '.xlsx, .xls'}),
        help_text="Upload .xlsx file following the template structure."
    )
