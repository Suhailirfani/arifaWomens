from django.shortcuts import render
from academics.models import SchoolClass, GradeLevel, Course
from students.models import Student
from staff.models import StaffProfile

def home_view(request):
    total_students = Student.objects.filter(is_active=True).count()
    total_staff = StaffProfile.objects.filter(is_active=True).count()
    classes = SchoolClass.objects.select_related('grade', 'course').all()

    context = {
        'total_students': total_students,
        'total_staff': total_staff,
        'classes': classes,
    }
    return render(request, 'home.html', context)
