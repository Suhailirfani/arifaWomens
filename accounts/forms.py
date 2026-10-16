from django import forms
from django.contrib.auth.forms import AuthenticationForm
from .models import User

class CustomLoginForm(AuthenticationForm):
    username = forms.CharField(
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter Username or Employee / Adm ID',
            'id': 'login-username'
        })
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter your password',
            'id': 'login-password'
        })
    )
