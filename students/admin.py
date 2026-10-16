from django.contrib import admin
from .models import Student

@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    list_display = ('admission_number', 'roll_number', 'full_name', 'current_class', 'father_or_guardian_name', 'guardian_phone', 'vehicle_opted', 'is_active')
    list_filter = ('current_class__grade', 'current_class__course', 'current_class', 'vehicle_opted', 'is_active')
    search_fields = ('admission_number', 'roll_number', 'full_name', 'guardian_phone', 'father_or_guardian_name')
