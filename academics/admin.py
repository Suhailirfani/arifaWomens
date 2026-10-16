from django.contrib import admin
from .models import AcademicYear, GradeLevel, Course, SchoolClass, Subject

@admin.register(AcademicYear)
class AcademicYearAdmin(admin.ModelAdmin):
    list_display = ('name', 'start_date', 'end_date', 'is_current')
    list_filter = ('is_current',)

@admin.register(GradeLevel)
class GradeLevelAdmin(admin.ModelAdmin):
    list_display = ('name', 'level_category', 'sequence')
    list_filter = ('level_category',)

@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ('name', 'code')
    search_fields = ('name', 'code')

@admin.register(SchoolClass)
class SchoolClassAdmin(admin.ModelAdmin):
    list_display = ('display_name', 'grade', 'course', 'section', 'academic_year', 'class_teacher', 'room_number')
    list_filter = ('academic_year', 'grade', 'course', 'section')
    search_fields = ('grade__name', 'course__name', 'section', 'room_number')

@admin.register(Subject)
class SubjectAdmin(admin.ModelAdmin):
    list_display = ('name', 'code')
    search_fields = ('name', 'code')
    filter_horizontal = ('school_classes',)
