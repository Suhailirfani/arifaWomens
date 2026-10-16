from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User

@admin.register(User)
class CustomUserAdmin(UserAdmin):
    list_display = ('username', 'email', 'first_name', 'last_name', 'role', 'phone_number', 'is_staff')
    list_filter = ('role', 'is_staff', 'is_superuser', 'is_active')
    fieldsets = UserAdmin.fieldsets + (
        ('Custom Profile Information', {
            'fields': ('role', 'phone_number', 'avatar'),
        }),
    )
    add_fieldsets = UserAdmin.add_fieldsets + (
        ('Custom Profile Information', {
            'fields': ('role', 'phone_number', 'avatar'),
        }),
    )
