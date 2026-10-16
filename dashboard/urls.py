from django.urls import path
from . import views

app_name = 'dashboard'

urlpatterns = [
    path('admin/', views.admin_dashboard, name='admin_dashboard'),
    path('staff/', views.staff_dashboard, name='staff_dashboard'),
    path('teacher/', views.teacher_dashboard, name='teacher_dashboard'),
    path('student/', views.student_dashboard, name='student_dashboard'),
    path('student/<int:student_id>/', views.student_dashboard, name='student_dashboard_detail'),
    path('class/<int:class_id>/', views.class_dashboard, name='class_dashboard'),
]
