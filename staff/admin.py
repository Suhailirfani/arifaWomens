from django.contrib import admin
from .models import StaffProfile

@admin.register(StaffProfile)
class StaffProfileAdmin(admin.ModelAdmin):
    list_display = ('staff_id', 'full_name', 'designation', 'department', 'phone', 'email', 'is_active')
    list_filter = ('designation', 'department', 'is_active', 'gender')
    search_fields = ('staff_id', 'full_name', 'phone', 'email', 'qualification')
    filter_horizontal = ('subjects_taught',)
