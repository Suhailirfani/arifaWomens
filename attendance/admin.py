from django.contrib import admin
from .models import DailyAttendanceSession, StudentAttendanceRecord

class StudentAttendanceRecordInline(admin.TabularInline):
    model = StudentAttendanceRecord
    extra = 0
    fields = ('student', 'status', 'remarks')

@admin.register(DailyAttendanceSession)
class DailyAttendanceSessionAdmin(admin.ModelAdmin):
    list_display = ('school_class', 'date', 'taken_by', 'total_students', 'present_count', 'absent_count', 'attendance_rate')
    list_filter = ('school_class', 'date')
    inlines = [StudentAttendanceRecordInline]

@admin.register(StudentAttendanceRecord)
class StudentAttendanceRecordAdmin(admin.ModelAdmin):
    list_display = ('student', 'session', 'status', 'remarks')
    list_filter = ('status', 'session__school_class', 'session__date')
    search_fields = ('student__full_name', 'student__admission_number')
