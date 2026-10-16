from django.contrib import admin
from .models import Exam, ExamSchedule, StudentMark

class ExamScheduleInline(admin.TabularInline):
    model = ExamSchedule
    extra = 1

@admin.register(Exam)
class ExamAdmin(admin.ModelAdmin):
    list_display = ('name', 'academic_year', 'start_date', 'end_date', 'is_published')
    list_filter = ('academic_year', 'is_published')
    inlines = [ExamScheduleInline]

@admin.register(ExamSchedule)
class ExamScheduleAdmin(admin.ModelAdmin):
    list_display = ('exam', 'school_class', 'subject', 'exam_date', 'max_marks', 'pass_marks')
    list_filter = ('exam', 'school_class')

@admin.register(StudentMark)
class StudentMarkAdmin(admin.ModelAdmin):
    list_display = ('student', 'exam_schedule', 'marks_obtained', 'is_absent', 'letter_grade')
    list_filter = ('exam_schedule__exam', 'exam_schedule__school_class', 'is_absent')
    search_fields = ('student__full_name', 'student__admission_number')
