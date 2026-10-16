from django.urls import path
from . import views

app_name = 'attendance'

urlpatterns = [
    path('take/', views.take_attendance, name='take_attendance'),
    path('history/', views.attendance_history, name='attendance_history'),
    path('history/', views.attendance_history, name='history'),
    path('api/student/<int:student_id>/heatmap/', views.api_student_heatmap, name='api_student_heatmap'),
]
