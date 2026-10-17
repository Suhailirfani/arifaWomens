from django import forms
from .models import StaffProfile

class StaffProfileForm(forms.ModelForm):
    create_login_account = forms.BooleanField(
        required=False,
        initial=True,
        label="Create Staff Portal Login Account",
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )
    ROLE_CHOICES = [
        ('teacher', 'Teacher / Faculty Portal'),
        ('office_staff', 'Office & Administrative Staff Portal'),
        ('admin', 'Administrator Portal'),
    ]
    login_role = forms.ChoiceField(
        choices=ROLE_CHOICES,
        required=False,
        initial='teacher',
        label="Portal Access Role",
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    username = forms.CharField(
        required=False,
        max_length=150,
        label="Portal Username",
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Default: Staff ID (e.g. ARF-STF-05)'
        }),
        help_text="Leave blank to automatically use the Staff ID as the username."
    )
    password = forms.CharField(
        required=False,
        max_length=128,
        label="Portal Password",
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Default: staff123'
        }),
        help_text="Leave blank to use default 'staff123' (or keep current on edit)."
    )

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


class StaffBulkUploadForm(forms.Form):
    excel_file = forms.FileField(
        widget=forms.FileInput(attrs={'class': 'form-control', 'accept': '.xlsx, .xls'}),
        help_text="Upload .xlsx file following the Staff template structure."
    )
