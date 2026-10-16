from django import forms
from .models import StaffProfile

class StaffProfileForm(forms.ModelForm):
    class Meta:
        model = StaffProfile
        fields = [
            'staff_id', 'full_name', 'gender', 'designation', 'department',
            'qualification', 'phone', 'email', 'address', 'joining_date',
            'is_active', 'photo', 'subjects_taught'
        ]
        widgets = {
            'staff_id': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. ARF-STF-05'}),
            'full_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Full Name'}),
            'gender': forms.Select(attrs={'class': 'form-select'}),
            'designation': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. Senior Lecturer, Office Assistant'}),
            'department': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. Humanities, Commerce, Administration'}),
            'qualification': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. M.A., B.Ed, M.Com'}),
            'phone': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Phone Number'}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Email Address'}),
            'address': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Address'}),
            'joining_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'subjects_taught': forms.SelectMultiple(attrs={'class': 'form-select', 'size': 5}),
        }
